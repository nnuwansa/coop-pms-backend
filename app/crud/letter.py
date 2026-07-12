from logging import getLogger

from sqlalchemy import exists, select, and_, func
from sqlalchemy.orm import Session

from db.models.models import Letter, Status, SystemUser, Department,LetterAssignee,LetterDepartment
from exception.exception import NoDataFoundException
from models.letter import LetterFilter
from models.system_user import SystemUserWithPermissionsModelOut

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


# async def get_all_letter(
#         offset: int,
#         limit: int,
#         filters: LetterFilter,
#         current_user: SystemUserWithPermissionsModelOut,
#         db: Session
# ):
#     conditions = [Letter.is_active]
#
#     if 'letter.view:department' in current_user.permissions:
#         conditions.append(LetterDepartment.department_id == current_user.department_id)
#     elif 'letter.view:self' in current_user.permissions:
#         conditions.append(LetterAssignee.assignee_id == current_user.id)
#     elif 'letter.view:all' in current_user.permissions:
#         if filters.department_id:
#             conditions.append(LetterDepartment.department_id == filters.department_id)
#         if filters.assignee_id:
#             conditions.append(LetterAssignee.assignee_id == filters.assignee_id)
#     else:
#         return 0, []
#
#     if filters.id:
#         conditions.append(Letter.id == filters.id)
#     if filters.code:
#         conditions.append(Letter.code.ilike(f"%{filters.code}%"))
#     if filters.subject:
#         conditions.append(Letter.subject.ilike(f"%{filters.subject}%"))
#     if filters.status_id:
#         conditions.append(Letter.status_id == filters.status_id)
#     if filters.organization_id:
#         conditions.append(Letter.organization_id == filters.organization_id)
#     if filters.create_date_start and filters.create_date_end:
#         conditions.append(
#             Letter.received_datetime.between(
#                 filters.create_date_start,
#                 filters.create_date_end
#             )
#         )
#     if filters.other:
#         conditions.append(Letter.other.ilike(f"%{filters.other}%"))
#
#     stmt = (
#         select(Letter)
#         .where(and_(*conditions))
#         .order_by(Letter.create_datetime.desc())
#         .offset(offset)
#         .limit(limit)
#     )
#
#     total_stmt = select(func.count(Letter.code.distinct())).select_from(Letter).where(and_(*conditions))
#
#     result = db.execute(stmt)
#     total_result = db.execute(total_stmt)
#
#     letters = result.scalars().all()
#     total = total_result.scalar_one()
#
#     return total, letters
from sqlalchemy.orm import joinedload

# async def get_all_letter(
#         offset: int,
#         limit: int,
#         filters: LetterFilter,
#         current_user: SystemUserWithPermissionsModelOut,
#         db: Session
# ):
#     conditions = [Letter.is_active]
#
#     needs_dept_join = False
#     needs_assignee_join = False
#
#     if 'letter.view:department' in current_user.permissions:
#         conditions.append(LetterDepartment.department_id == current_user.department_id)
#         needs_dept_join = True
#     elif 'letter.view:self' in current_user.permissions:
#         conditions.append(LetterAssignee.assignee_id == current_user.id)
#         needs_assignee_join = True
#     elif 'letter.view:all' in current_user.permissions:
#         if filters.department_id:
#             conditions.append(LetterDepartment.department_id == filters.department_id)
#             needs_dept_join = True
#         if filters.assignee_id:
#             conditions.append(LetterAssignee.assignee_id == filters.assignee_id)
#             needs_assignee_join = True
#     else:
#         return 0, []
#
#     if filters.id:
#         conditions.append(Letter.id == filters.id)
#     if filters.code:
#         conditions.append(Letter.code.ilike(f"%{filters.code}%"))
#     if filters.subject:
#         conditions.append(Letter.subject.ilike(f"%{filters.subject}%"))
#     if filters.status_id:
#         conditions.append(Letter.status_id == filters.status_id)
#     if filters.organization_id:
#         conditions.append(Letter.organization_id == filters.organization_id)
#     if filters.create_date_start and filters.create_date_end:
#         conditions.append(
#             Letter.received_datetime.between(
#                 filters.create_date_start,
#                 filters.create_date_end
#             )
#         )
#     if filters.other:
#         conditions.append(Letter.other.ilike(f"%{filters.other}%"))
#
#     query = select(Letter.id).distinct()
#     if needs_dept_join:
#         query = query.join(LetterDepartment, LetterDepartment.letter_id == Letter.id)
#     if needs_assignee_join:
#         query = query.join(LetterAssignee, LetterAssignee.letter_id == Letter.id)
#     query = query.where(and_(*conditions))
#
#     total_stmt = select(func.count()).select_from(query.subquery())
#     total = db.execute(total_stmt).scalar_one()
#
#     id_stmt = query.order_by(None).offset(offset).limit(limit)
#     ids_result = db.execute(id_stmt).scalars().all()
#
#     if not ids_result:
#         return total, []
#
#     letters = (
#         db.query(Letter)
#         .filter(Letter.id.in_(ids_result))
#         .order_by(Letter.create_datetime.desc())
#         .all()
#     )
#
#     return total, letters

from sqlalchemy.orm import joinedload

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

    if 'letter.view:department' in current_user.permissions:
        conditions.append(LetterDepartment.department_id == current_user.department_id)
        needs_dept_join = True
    elif 'letter.view:self' in current_user.permissions:
        conditions.append(LetterAssignee.assignee_id == current_user.id)
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
    if filters.create_date_start and filters.create_date_end:
        conditions.append(
            Letter.received_datetime.between(
                filters.create_date_start,
                filters.create_date_end
            )
        )
    if filters.other:
        conditions.append(Letter.other.ilike(f"%{filters.other}%"))

    # NOTE: select id + create_datetime together (not id alone) so that
    # ORDER BY create_datetime is valid alongside SELECT DISTINCT (Postgres
    # requires ORDER BY expressions to appear in the select list when DISTINCT is used).
    id_query = select(Letter.id, Letter.create_datetime).distinct()
    if needs_dept_join:
        id_query = id_query.join(LetterDepartment, LetterDepartment.letter_id == Letter.id)
    if needs_assignee_join:
        id_query = id_query.join(LetterAssignee, LetterAssignee.letter_id == Letter.id)
    id_query = id_query.where(and_(*conditions))

    total_stmt = select(func.count()).select_from(
        id_query.with_only_columns(Letter.id).subquery()
    )
    total = db.execute(total_stmt).scalar_one()

    # ✅ Explicit, deterministic order: newest first, id as tiebreaker
    id_stmt = (
        id_query
        .order_by(Letter.create_datetime.desc(), Letter.id.desc())
        .offset(offset)
        .limit(limit)
    )
    ids_result = [row[0] for row in db.execute(id_stmt).all()]

    if not ids_result:
        return total, []

    letters = (
        db.query(Letter)
        .filter(Letter.id.in_(ids_result))
        .order_by(Letter.create_datetime.desc())
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


async def update_letter_attribute(
        letter: Letter,
        attribute: str,
        new_id: int,
        db: Session
) -> Letter:
    setattr(letter, f"{attribute}_id", new_id)
    db.commit()
    db.refresh(letter)
    return letter


async def letters_excel_data(db, current_user, filters):
    conditions = [Letter.is_active]
    if 'letter.view:department' in current_user.permissions:
        conditions.append(LetterDepartment.department_id == current_user.department_id)
    elif 'letter.view:self' in current_user.permissions:
        conditions.append(LetterAssignee.assignee_id == current_user.id)
    elif 'letter.view:all' not in current_user.permissions:
        return []

    query = db.query(Letter).filter(and_(*conditions))
    if filters.create_date_start:
        query = query.filter(Letter.received_datetime >= filters.create_date_start)
    if filters.create_date_end:
        query = query.filter(Letter.received_datetime <= filters.create_date_end)
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


# async def get_all_status_counts(current_user: SystemUserWithPermissionsModelOut, db: Session):
#     conditions = [Letter.is_active]
#     if 'letter.view:department' in current_user.permissions:
#         conditions.append(LetterDepartment.department_id == current_user.department_id)
#     elif 'letter.view:self' in current_user.permissions:
#         conditions.append(LetterAssignee.assignee_id == current_user.id)
#     elif 'letter.view:all' not in current_user.permissions:
#         return []
#
#     result = db.execute(
#         select(Status.id, Status.name, func.count(Letter.id).label("letter_count"))
#         .outerjoin(Letter, Status.id == Letter.status_id)
#         .where(and_(*conditions))
#         .group_by(Status.id, Status.name)
#     )
#     status_counts = result.all()
#     return status_counts


async def get_all_status_counts(current_user: SystemUserWithPermissionsModelOut, db: Session):
    conditions = [Letter.is_active]
    needs_dept_join = False
    needs_assignee_join = False

    if 'letter.view:department' in current_user.permissions:
        conditions.append(LetterDepartment.department_id == current_user.department_id)
        needs_dept_join = True
    elif 'letter.view:self' in current_user.permissions:
        conditions.append(LetterAssignee.assignee_id == current_user.id)
        needs_assignee_join = True
    elif 'letter.view:all' not in current_user.permissions:
        return []

    query = (
        select(Status.id, Status.name, func.count(func.distinct(Letter.id)).label("letter_count"))
        .select_from(Status)
        .outerjoin(Letter, Status.id == Letter.status_id)
    )
    if needs_dept_join:
        query = query.join(LetterDepartment, LetterDepartment.letter_id == Letter.id)
    if needs_assignee_join:
        query = query.join(LetterAssignee, LetterAssignee.letter_id == Letter.id)

    query = query.where(and_(*conditions)).group_by(Status.id, Status.name)

    result = db.execute(query)
    return result.all()