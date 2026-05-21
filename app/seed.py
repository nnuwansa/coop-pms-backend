import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '../.env.production'))
from db.session import engine
from sqlalchemy import text


with engine.connect() as conn:
    conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
    
    conn.execute(text("""INSERT INTO permission (name, code, description, category, action, create_datetime) VALUES
('View Own Letters','letter.view:self','Can view only letters assigned to the user','Letter Management View','radio',NOW()),
('View Department Letters','letter.view:department','Can view letters within the users department','Letter Management View','radio',NOW()),
('View All Letters','letter.view:all','Can view all letters regardless of department','Letter Management View','radio',NOW()),
('Create Letter','letter.create','Can create a new letter','Letter Management','check',NOW()),
('Update Letter','letter.update','Can edit a letter','Letter Management','check',NOW()),
('Delete Letter','letter.delete','Can delete a letter','Letter Management','check',NOW()),
('Assign Letter','letter.assign','Can change the assignee of a letter','Letter Management','check',NOW()),
('Change Letter Department','letter.change_department','Can change the letters department','Letter Management','check',NOW()),
('Change Letter Status','letter.change_status','Can change the letters status','Letter Management','check',NOW()),
('View Letter History','letter.history','Can view letter history','Letter Management','check',NOW()),
('Duplicate Letter','letter.duplicate','Can duplicate a letter','Letter Management','check',NOW()),
('Download Letter','letter.download','Can download the letter as PDF','Letter Management','check',NOW()),
('Download List of Letters','letter.xdownload','Can download list of letters as excel','Letter Management','check',NOW()),
('View Remarks','remark.view','Can view remarks','Remark Management','check',NOW()),
('Create Remark','remark.create','Can add a remark','Remark Management','check',NOW()),
('Update Remark','remark.update','Can edit a remark','Remark Management','check',NOW()),
('Delete Remark','remark.delete','Can delete a remark','Remark Management','check',NOW()),
('Manage User Details','user.view','Can view update delete user details','User Management','check',NOW()),
('Manage System Settings','settings.view','Can view update delete system settings','System Settings','check',NOW())"""))

    conn.execute(text("""INSERT INTO role (id, name, description, update_datetime, create_datetime, is_active) VALUES
(1, 'Administrator', 'Full system access', NOW(), NOW(), 1)"""))

    perms = conn.execute(text("SELECT id, code FROM permission")).fetchall()
    perm_ids = [p[0] for p in perms]
    print("Permission IDs:", perm_ids)

    for pid in perm_ids[2:]:
        conn.execute(text(f"INSERT INTO role_permission (role_id, permission_id) VALUES (1, {pid})"))

    conn.execute(text("""INSERT INTO system_user (email, first_name, last_name, password, role_id, department_id, update_datetime, create_datetime, is_active)
VALUES ('systemadmin@pms.coop', 'System', 'Admin', '$2b$12$5O0wJhpwbsiUruL1PU7vaO4o/kiMVTF/hHFNXGYALLx2zMiNB04q2', 1, 1, NOW(), NOW(), 1)"""))

    conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))
    conn.commit()
    print("Done! All data inserted.")