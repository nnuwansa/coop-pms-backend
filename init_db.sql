INSERT INTO `organization` (`name`, `update_datetime`, `create_datetime`, `is_active`)
VALUES ('A. Baur & Co. (Pvt) Ltd.', NOW(), NOW(), 1),
       ('MAS Holdings (Private) Limited', NOW(), NOW(), 1),
       ('Brandix Apparel (Pvt) Ltd', NOW(), NOW(), 1),
       ('Access Engineering PLC', NOW(), NOW(), 1),
       ('Dilmah Ceylon Tea Company PLC', NOW(), NOW(), 1);

INSERT INTO `source` (`name`, `update_datetime`, `create_datetime`, `is_active`)
VALUES ('Post', NOW(), NOW(), 1),
       ('Registered Post', NOW(), NOW(), 1),
       ('Email', NOW(), NOW(), 1),
       ('Whatsapp', NOW(), NOW(), 1),
       ('By Hand', NOW(), NOW(), 1),
       ('Fax', NOW(), NOW(), 1),
       ('Money Order', NOW(), NOW(), 1),
       ('Cheque', NOW(), NOW(), 1);

INSERT INTO `department` (`name`, `update_datetime`, `create_datetime`, `is_active`)
VALUES ('Department of Finance', NOW(), NOW(), 1),
       ('Department of Health', NOW(), NOW(), 1),
       ('Department of Education', NOW(), NOW(), 1),
       ('Department of Transportation', NOW(), NOW(), 1),
       ('Department of Agriculture', NOW(), NOW(), 1);

INSERT INTO `status` (`name`, `update_datetime`, `create_datetime`, `is_active`)
VALUES ('New', NOW(), NOW(), 1),
       ('Assigned', NOW(), NOW(), 1),
       ('In Progress', NOW(), NOW(), 1),
       ('Rejected', NOW(), NOW(), 1),
       ('Completed', NOW(), NOW(), 1),
       ('Approved', NOW(), NOW(), 1),
       ('On Hold', NOW(), NOW(), 1),
       ('Replied - Final', NOW(), NOW(), 1),
       ('Replied - Interim', NOW(), NOW(), 1),
       ('Not Relevant', NOW(), NOW(), 1),
       ('Report Requested', NOW(), NOW(), 1),
       ('Closed', NOW(), NOW(), 1);

INSERT INTO `permission` (`name`, `code`, `description`, `category`, `action`, `create_datetime`) VALUES
('View Own Letters', 'letter.view:self', 'Can view only letters assigned to the user', 'Letter Management View', 'radio', NOW()),
('View Department Letters', 'letter.view:department', 'Can view letters within the user\'s department', 'Letter Management View', 'radio', NOW()),
('View All Letters', 'letter.view:all', 'Can view all letters regardless of department', 'Letter Management View', 'radio', NOW()),
('Create Letter', 'letter.create', 'Can create a new letter', 'Letter Management', 'check', NOW()),
('Update Letter', 'letter.update', 'Can edit a letter', 'Letter Management', 'check', NOW()),
('Delete Letter', 'letter.delete', 'Can delete a letter', 'Letter Management', 'check', NOW()),
('Assign Letter', 'letter.assign', 'Can change the assignee of a letter', 'Letter Management', 'check', NOW()),
('Change Letter Department', 'letter.change_department', 'Can change the letter’s department', 'Letter Management', 'check', NOW()),
('Change Letter Status', 'letter.change_status', 'Can change the letter\'s status', 'Letter Management', 'check', NOW()),
('View Letter History', 'letter.history', 'Can view letter history/audit trail', 'Letter Management', 'check', NOW()),
('Duplicate Letter', 'letter.duplicate', 'Can duplicate a letter', 'Letter Management', 'check', NOW()),
('Download Letter', 'letter.download', 'Can download the letter as PDF file', 'Letter Management', 'check', NOW()),
('Download List of Letters', 'letter.xdownload', 'Can download list of letters as excel file', 'Letter Management', 'check', NOW()),
('View Remarks', 'remark.view', 'Can view remarks', 'Remark Management', 'check', NOW()),
('Create Remark', 'remark.create', 'Can add a remark to a letter', 'Remark Management', 'check', NOW()),
('Update Remark', 'remark.update', 'Can edit a remark', 'Remark Management', 'check', NOW()),
('Delete Remark', 'remark.delete', 'Can delete a remark', 'Remark Management', 'check', NOW()),
('Manage User Details', 'user.view', 'Can view /update /delete user details', 'User Management', 'check', NOW()),
('Manage System Settings', 'settings.view', 'Can view /update /delete system settings', 'System Settings', 'check', NOW());

INSERT INTO `role` (`id`, `name`, `description`, `update_datetime`, `create_datetime`, `is_active`) VALUES
(1, 'Administrator', 'Full system access', NOW(), NOW(), 1);

INSERT INTO `role_permission` (`role_id`, `permission_id`) VALUES
(1, 3),
(1, 4),
(1, 5),
(1, 6),
(1, 7),
(1, 8),
(1, 9),
(1, 10),
(1, 11),
(1, 12),
(1, 13),
(1, 14),
(1, 15),
(1, 16),
(1, 17),
(1, 18),
(1, 19);

-- systemadmin@pms.coop
-- Systemadmin@1
INSERT INTO `system_user` (`email`, `first_name`, `last_name`, `password`, `role_id`, `department_id`,
                           `update_datetime`, `create_datetime`, `is_active`)
VALUES ('systemadmin@pms.coop', 'System', 'Admin', '$2b$12$5O0wJhpwbsiUruL1PU7vaO4o/kiMVTF/hHFNXGYALLx2zMiNB04q2', 1, 1, NOW(), NOW(), 1),
       ('john.doe@gov.example', 'John', 'Doe', 'Pass@123', NULL, 1, NOW(), NOW(), 1),
       ('jane.smith@gov.example', 'Jane', 'Smith', 'Secure#456', NULL, 2, NOW(), NOW(), 1),
       ('michael.lee@gov.example', 'Michael', 'Lee', 'Admin!789', NULL, 3, NOW(), NOW(), 1),
       ('emma.johnson@gov.example', 'Emma', 'Johnson', 'Welcome$321', NULL, 4, NOW(), NOW(), 1),
       ('david.wilson@gov.example', 'David', 'Wilson', 'Gov@2024', NULL, 5, NOW(), NOW(), 1);
