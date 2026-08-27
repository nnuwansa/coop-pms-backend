from logging import getLogger
from datetime import datetime, timedelta

from sqlalchemy import exists, select, and_, or_, func
from sqlalchemy.orm import Session

from db.models.models import Letter, Status, SystemUser, Department, LetterAssignee, LetterDepartment, LetterAssigneeStatus
from exception.exception import NoDataFoundException
from models.letter import LetterFilter
from models.system_user import SystemUserWithPermissionsModelOut
from sqlalchemy.orm import joinedload, aliased

logger = getLogger(__name__)


async def save_letter(letter: Letter, db: Session) -> Letter:
    db.add(letter)
    db.commit()
    db.refresh(letter)
    return letter


async def get_active_letter(letter_id: int, db: Session) -> Letter | None:
    letter = db.query(Letter).filter(and_(Letter.id == letter_id, Letter.is_active)).first()
    return letter


async def code_exist(code: str, db: Session) -> bool:
    stmt = select(exists().where(and_(Letter.code == code, Letter.is_active)))
    result = db.scalar(stmt)
    return result


async def update_letter(letter: Letter, db: Session) -> Letter:
    db.commit()
    db.refresh(letter)
    return letter


async def get_all_letter(
        offset: int,
        limit: int,
        filters: LetterFilter,
        current_user: SystemUserWithPermissionsModelOut,
        db: Session
):
    conditions = [Letter.is_active]

    needs_dept_join = False
    needs_assignee_join = False
    needs_status_join = False  # NEW — for the pending_only filter, which needs to check Status.name

    # NEW — department/unit accounts (is_department_account=True) have no
    # role, so they carry no permissions. They see only letters routed to
    # their own unit (or, if they're a plain department account with no
    # unit, their department with no unit set) — this is checked before
    # the permission-based branches so it applies regardless of role.
    if getattr(current_user, "is_department_account", False):
        if current_user.department_unit_id:
            conditions.append(LetterDepartment.department_unit_id == current_user.department_unit_id)
        else:
            conditions.append(
                and_(
                    LetterDepartment.department_id == current_user.department_id,
                    LetterDepartment.department_unit_id.is_(None)
                )
            )
        needs_dept_join = True

    elif 'letter.view:department' in current_user.permissions:
        conditions.append(
            or_(
                LetterDepartment.department_id == current_user.department_id,
                LetterAssignee.assignee_id == current_user.id,
                Letter.recommended_to_id == current_user.id,
                Letter.forwarded_to_id == current_user.id,
            )
        )
        needs_dept_join = True
        needs_assignee_join = True

    elif 'letter.view:self' in current_user.permissions:
        conditions.append(
            or_(
                LetterAssignee.assignee_id == current_user.id,
                Letter.recommended_to_id == current_user.id,
                Letter.forwarded_to_id == current_user.id,
            )
        )
        needs_assignee_join = True
    elif 'letter.view:all' in current_user.permissions:
        if filters.department_id:
            conditions.append(LetterDepartment.department_id == filters.department_id)
            needs_dept_join = True
        if filters.assignee_id:
            conditions.append(LetterAssignee.assignee_id == filters.assignee_id)
            needs_assignee_join = True
    else:
        return 0, []

    # NEW — explicit ID selection (e.g. checkboxes ticked in the dashboard
    # table). This takes priority over all other search filters below: it's
    # an exact "give me these specific letters" request, so combining it
    # with code/subject/status/org/date-range filters that weren't meant to
    # apply to a manual selection would silently drop rows the user picked.
    # Permission-based visibility conditions above still apply.
    if filters.ids:
        conditions.append(Letter.id.in_(filters.ids))
    else:
        if filters.id:
            conditions.append(Letter.id == filters.id)
        if filters.code:
            conditions.append(Letter.code.ilike(f"%{filters.code}%"))
        if filters.subject:
            conditions.append(Letter.subject.ilike(f"%{filters.subject}%"))
        if filters.status_id:
            conditions.append(Letter.status_id == filters.status_id)
        if filters.organization_id:
            conditions.append(Letter.organization_id == filters.organization_id)
        if filters.create_date_start:
            conditions.append(Letter.received_datetime >= filters.create_date_start)
        if filters.create_date_end:
            conditions.append(Letter.received_datetime <= filters.create_date_end)
        if filters.other:
            conditions.append(Letter.other.ilike(f"%{filters.other}%"))
        # NEW — "Has Cheque/Money Order" filter: only letters where a
        # cheque/money order number was actually recorded.
        if filters.has_cheque:
            conditions.append(and_(Letter.other.isnot(None), Letter.other != ''))
        if filters.is_public_complaint is not None:
               conditions.append(Letter.is_public_complaint == filters.is_public_complaint)

        # CHANGED — "Pending only" filter now matches the same completion
        # rule used for the days_pending badge: a letter with assignees
        # counts as done only once EVERY assignee's own status is
        # "Completed" (per-assignee LetterAssigneeStatus rows), not the
        # letter's overall status column, which per-assignee statuses don't
        # keep in sync. Letters with no assignees fall back to the old rule
        # (checking the letter's own overall status).
        if filters.pending_only:
            AssigneeStatusTable = aliased(Status)  # avoid clashing with the outer Status join used for the letter-level fallback
            not_completed_assignee_exists = exists(
                select(LetterAssigneeStatus.id)
                .join(AssigneeStatusTable, AssigneeStatusTable.id == LetterAssigneeStatus.status_id)
                .where(
                    LetterAssigneeStatus.letter_id == Letter.id,
                    AssigneeStatusTable.name != 'Completed',
                )
            )
            has_any_assignee_status = exists(
                select(LetterAssigneeStatus.id).where(LetterAssigneeStatus.letter_id == Letter.id)
            )
            conditions.append(
                or_(
                    and_(has_any_assignee_status, not_completed_assignee_exists),
                    and_(~has_any_assignee_status, or_(Letter.status_id.is_(None), Status.name != 'Completed')),
                )
            )
            needs_status_join = True

            # NEW — days-pending range, e.g. "1-5 days pending". Since a
            # pending letter's days_pending is simply (now - received_datetime)
            # in whole days (see service/letter.py's _days_pending), we can
            # express "days_pending between min and max" directly as a
            # received_datetime window, without needing a raw day-diff
            # expression in SQL:
            #   days_pending >= min  <=>  received_datetime <= now - min days
            #   days_pending <= max  <=>  received_datetime >= now - max days
            if filters.pending_days_min is not None:
                conditions.append(
                    Letter.received_datetime <= (datetime.utcnow() - timedelta(days=filters.pending_days_min))
                )
            if filters.pending_days_max is not None:
                conditions.append(
                    Letter.received_datetime >= (datetime.utcnow() - timedelta(days=filters.pending_days_max))
                )

        # NEW — filter by an individual ASSIGNEE'S status rather than the
        # letter's overall status (the dashboard no longer shows/relies on
        # the overall status column). Matches any letter where at least one
        # assignee currently has this status.
        if filters.assignee_status_id:
            conditions.append(
                exists(
                    select(LetterAssigneeStatus.id).where(
                        LetterAssigneeStatus.letter_id == Letter.id,
                        LetterAssigneeStatus.status_id == filters.assignee_status_id,
                    )
                )
            )

    # NOTE: select id + received_datetime together (not id alone) so that
    # ORDER BY received_datetime is valid alongside SELECT DISTINCT (Postgres
    # requires ORDER BY expressions to appear in the select list when DISTINCT is used).
    # CHANGED — was Letter.create_datetime. Sorting by the DB row's actual
    # insertion time meant a letter entered late for an old Received Date
    # sorted as "newest" (since it was just inserted), instead of appearing
    # in its correct place by Received Date. received_datetime is what the
    # "Received Date" column actually shows, so that's what we sort by.
    id_query = select(Letter.id, Letter.received_datetime).distinct()
    if needs_dept_join:
        id_query = id_query.outerjoin(LetterDepartment, LetterDepartment.letter_id == Letter.id)
    if needs_assignee_join:
        id_query = id_query.outerjoin(LetterAssignee, LetterAssignee.letter_id == Letter.id)
    if needs_status_join:
        id_query = id_query.outerjoin(Status, Status.id == Letter.status_id)
    id_query = id_query.where(and_(*conditions))

    total_stmt = select(func.count()).select_from(
        id_query.with_only_columns(Letter.id).subquery()
    )
    total = db.execute(total_stmt).scalar_one()

    # Explicit, deterministic order: newest RECEIVED first, id as tiebreaker.
    # NEW — when filters.ids is set, skip offset/limit entirely: the caller
    # asked for exactly these IDs, so pagination shouldn't be able to cut
    # any of them out (e.g. if the frontend's page_size guess ever drifts
    # from len(ids)).
    id_stmt = id_query.order_by(Letter.received_datetime.desc(), Letter.id.desc())
    if not filters.ids:
        id_stmt = id_stmt.offset(offset).limit(limit)
    ids_result = [row[0] for row in db.execute(id_stmt).all()]

    if not ids_result:
        return total, []

    letters = (
        db.query(Letter)
        .filter(Letter.id.in_(ids_result))
        .order_by(Letter.received_datetime.desc())  # CHANGED — was create_datetime
        .all()
    )

    return total, letters

async def validate_attribute(attribute: str, entity_id: int, db: Session):
    model_map = {
        "status": Status,
        "assignee": SystemUser,
        "department": Department
    }

    model = model_map.get(attribute)
    if not model:
        raise NoDataFoundException("Invalid attribute type")

    return db.query(model).filter(and_(model.id == entity_id, model.is_active)).first()


async def update_letter_attribute(letter: Letter, attribute: str, new_id: int, db: Session) -> Letter:
    setattr(letter, f"{attribute}_id", new_id)
    if attribute == "status":
        from datetime import datetime
        letter.status_since = datetime.utcnow()   # NEW
    db.commit()
    db.refresh(letter)
    return letter


async def letters_excel_data(db, current_user, filters):
    conditions = [Letter.is_active]
    needs_dept_join = False
    needs_assignee_join = False

    # Permission-based visibility is always enforced, even when filters.ids
    # is set — an explicit ID list must never be able to bypass a user's
    # department/self view scoping.
    if 'letter.view:department' in current_user.permissions:
        conditions.append(
            or_(
                LetterDepartment.department_id == current_user.department_id,
                LetterAssignee.assignee_id == current_user.id,
                Letter.recommended_to_id == current_user.id,   # NEW
                Letter.forwarded_to_id == current_user.id,   # NEW — forwarded letters must be visible to their recipient too
            )
        )
        needs_dept_join = True
        needs_assignee_join = True
    elif 'letter.view:self' in current_user.permissions:
        conditions.append(
            or_(
                LetterAssignee.assignee_id == current_user.id,
                Letter.recommended_to_id == current_user.id,   # NEW
                Letter.forwarded_to_id == current_user.id,   # NEW — forwarded letters must be visible to their recipient too
            )
        )
        needs_assignee_join = True
    elif 'letter.view:all' not in current_user.permissions:
        return []

    query = db.query(Letter)
    if needs_dept_join:
        query = query.outerjoin(LetterDepartment, LetterDepartment.letter_id == Letter.id)
    if needs_assignee_join:
        query = query.outerjoin(LetterAssignee, LetterAssignee.letter_id == Letter.id)
    query = query.filter(and_(*conditions)).distinct()

    # NEW — explicit ID selection (e.g. checkboxes ticked in the dashboard
    # table) takes priority over limit/date-range: it's an exact "export
    # these specific letters" request. We return early here so a leftover
    # `limit` (e.g. from the export dialog's "Number of Entries" dropdown)
    # can never silently truncate a manual selection.
    if filters.ids:
        query = query.filter(Letter.id.in_(filters.ids))
        query = query.order_by(Letter.received_datetime.asc(), Letter.id.asc())
        return query.all()

    if filters.create_date_start:
        query = query.filter(Letter.received_datetime >= filters.create_date_start)
    if filters.create_date_end:
        query = query.filter(Letter.received_datetime <= filters.create_date_end)
    if filters.is_public_complaint is not None:
               query = query.filter(Letter.is_public_complaint == filters.is_public_complaint)
    # CHANGED — order_by() must come BEFORE limit()/offset() on this legacy
    # Query API; calling it after raised:
    #   sqlalchemy.exc.InvalidRequestError: Query.order_by() being called on
    #   a Query which already has LIMIT or OFFSET applied.
    # so it's now applied first, and the limit (if any) is applied after.
    query = query.order_by(Letter.received_datetime.asc(), Letter.id.asc())
    if filters.limit:
        query = query.limit(filters.limit)
    rows = query.all()
    return rows


async def get_letter_count(prefix: str, db: Session) -> int:
    result = db.execute(
        select(func.count(Letter.code.distinct()))
        .select_from(Letter)
        .where(Letter.code.startswith(prefix))
    )
    count = result.scalar_one()
    return count


async def get_all_status_counts(current_user: SystemUserWithPermissionsModelOut, db: Session):
    conditions = [Letter.is_active]
    needs_dept_join = False
    needs_assignee_join = False

    if 'letter.view:department' in current_user.permissions:
        conditions.append(
            or_(
                LetterDepartment.department_id == current_user.department_id,
                LetterAssignee.assignee_id == current_user.id,
                Letter.recommended_to_id == current_user.id,   # NEW
                Letter.forwarded_to_id == current_user.id,   # NEW — forwarded letters must be visible to their recipient too
            )
        )
        needs_dept_join = True
        needs_assignee_join = True
    elif 'letter.view:self' in current_user.permissions:
        conditions.append(
            or_(
                LetterAssignee.assignee_id == current_user.id,
                Letter.recommended_to_id == current_user.id,   # NEW
                Letter.forwarded_to_id == current_user.id,   # NEW — forwarded letters must be visible to their recipient too
            )
        )
        needs_assignee_join = True
    elif 'letter.view:all' not in current_user.permissions:
        return []

    query = (
        select(Status.id, Status.name, func.count(func.distinct(Letter.id)).label("letter_count"))
        .select_from(Status)
        .outerjoin(Letter, Status.id == Letter.status_id)
    )
    if needs_dept_join:
        query = query.outerjoin(LetterDepartment, LetterDepartment.letter_id == Letter.id)
    if needs_assignee_join:
        query = query.outerjoin(LetterAssignee, LetterAssignee.letter_id == Letter.id)

    query = query.where(and_(*conditions)).group_by(Status.id, Status.name)

    result = db.execute(query)
    return result.all()


async def get_last_letter_number(prefix: str, db: Session) -> int:
    """
    Returns the highest sequence number already used among ACTIVE codes
    starting with `prefix`, where `prefix` is the "T + year + month"
    portion only (e.g. "T202607").

    IMPORTANT: only `is_active` letters are considered. Deleting a letter
    sets `is_active = False` but keeps the row (and its code) in the
    table -- if we counted those rows here, deleting the most recent
    letter(s) would still "burn" their numbers, so the next generated
    code would skip ahead (e.g. jump straight to ...368 instead of
    reusing ...366) even though nothing with that number exists anymore.
    Filtering to active rows means the next number always continues
    right after the highest number still in use.

    The code format is "T" + year + month + day(2 digits) + number, so
    after `prefix` there are always exactly 2 more digits for the day
    before the number starts. We skip those 2 digits explicitly, which
    lets the sequence continue across days within the same month (e.g.
    last code on the 20th was ...350, first code on the 21st becomes 351)
    instead of resetting to 01 on a new day.

    We use MAX(suffix) instead of COUNT(*) / COUNT(DISTINCT): COUNT can
    fall out of sync with the "next number that should be used" whenever a
    code is reused -- e.g. `duplicate_letter` copies the original letter's
    code verbatim, so two rows can share the same code without increasing
    a distinct count. MAX+1 always gives a correct, strictly increasing
    next number regardless of gaps or duplicates.

    `with_for_update()` locks the matching rows for the duration of the
    transaction, so two letters being created at (almost) the same moment
    can't both compute the same "next number".
    """
    like_pattern = f"{prefix}%"
    rows = db.execute(
        select(Letter.code)
        .where(and_(Letter.code.like(like_pattern), Letter.is_active))
        .with_for_update()
    ).scalars().all()

    max_number = 0
    # skip the prefix (year+month) AND the 2-digit day that always follows it
    skip_len = len(prefix) + 2
    for code in rows:
        suffix = code[skip_len:]
        if suffix.isdigit():
            max_number = max(max_number, int(suffix))

    return max_number


# ─── Deleted Letters (soft-delete collection) ──────────────────────────────
# NEW — `Letter.is_active` was already used as the soft-delete flag
# everywhere else in this file. These functions work with the
# is_active=False rows specifically, so a deleted letter isn't just
# invisible — it lands in its own reviewable collection that an admin can
# restore from, or permanently purge from, instead of a delete being silent
# and effectively irreversible from the UI's point of view.

async def get_deleted_letters(offset: int, limit: int, db: Session):
    """Paginated list of soft-deleted (is_active=False) letters, newest deletion first."""
    base = select(Letter).where(Letter.is_active.is_(False))

    total = db.execute(
        select(func.count()).select_from(base.with_only_columns(Letter.id).subquery())
    ).scalar_one()

    stmt = base.order_by(Letter.update_datetime.desc()).offset(offset).limit(limit)
    letters = db.execute(stmt).scalars().all()

    return total, letters


async def get_deleted_letter(letter_id: int, db: Session) -> Letter | None:
    return db.query(Letter).filter(
        Letter.id == letter_id, Letter.is_active.is_(False)
    ).first()


async def restore_deleted_letter(letter: Letter, db: Session) -> Letter:
    letter.is_active = True
    db.commit()
    db.refresh(letter)
    return letter


async def permanently_delete_letter(letter_id: int, db: Session) -> None:
    """
    Actually removes a letter row and everything that references it.
    Deletion order matters here: child rows referencing letter_id via a
    foreign key must go first, or the delete would fail (or silently leave
    orphaned rows, depending on the DB's FK enforcement settings).
    """
    from db.models.models import (
        Remark, RemarkAttachment, RemarkHistory, LetterAttachment,
        History, LetterRelation,
    )

    remark_ids = [r.id for r in db.query(Remark.id).filter(Remark.letter_id == letter_id).all()]
    if remark_ids:
        db.query(RemarkAttachment).filter(RemarkAttachment.remark_id.in_(remark_ids)).delete(synchronize_session=False)
        db.query(RemarkHistory).filter(RemarkHistory.remark_id.in_(remark_ids)).delete(synchronize_session=False)
    db.query(Remark).filter(Remark.letter_id == letter_id).delete(synchronize_session=False)
    db.query(RemarkHistory).filter(RemarkHistory.letter_id == letter_id).delete(synchronize_session=False)

    db.query(LetterAttachment).filter(LetterAttachment.letter_id == letter_id).delete(synchronize_session=False)
    db.query(LetterAssignee).filter(LetterAssignee.letter_id == letter_id).delete(synchronize_session=False)
    db.query(LetterDepartment).filter(LetterDepartment.letter_id == letter_id).delete(synchronize_session=False)
    db.query(LetterAssigneeStatus).filter(LetterAssigneeStatus.letter_id == letter_id).delete(synchronize_session=False)
    db.query(History).filter(History.letter_id == letter_id).delete(synchronize_session=False)
    db.query(LetterRelation).filter(
        or_(LetterRelation.letter_id == letter_id, LetterRelation.related_letter_id == letter_id)
    ).delete(synchronize_session=False)

    db.query(Letter).filter(Letter.id == letter_id).delete(synchronize_session=False)
    db.commit()