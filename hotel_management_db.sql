/*
 * ==================================================================================
 * 酒店入住管理系统 - 完整数据库脚本
 * ==================================================================================
 *
 * 【文件说明】本文件是酒店入住管理系统的完整数据库结构和初始化数据脚本
 * 【数据库】hotel_management_db | 字符集: utf8mb4 | 引擎: InnoDB
 * 【默认账户】用户名: admin | 密码: admin | 权限: 超级管理员
 * 【更新日期】2025-12-13
 *
 * 【表结构】
 * - Django系统表: auth_*, django_* (用户认证、权限、会话、日志等)
 * - 业务表: customers_customer(客户), employees_employee(员工), rooms_room(房间)
 *          reservations_reservation(预订), finance_income(收入), finance_expense(支出)
 * ==================================================================================
 */

-- 设置字符编码为utf8mb4，支持中文和emoji
SET NAMES utf8mb4;
-- 临时禁用外键检查，方便按任意顺序创建表和导入数据
SET FOREIGN_KEY_CHECKS = 0;

-- ====================================================================================
-- 【表1】auth_group - 用户组表
-- 【功能】将用户按角色分组（如前台、财务、经理），便于统一管理权限
-- 【关联】通过auth_group_permissions关联权限，通过auth_user_groups关联用户
-- ====================================================================================
DROP TABLE IF EXISTS `auth_group`;
CREATE TABLE `auth_group` (
                              `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '组ID，主键自增',
                              `name` varchar(150) NOT NULL COMMENT '组名称，如"前台组"、"财务组"，必须唯一',
                              PRIMARY KEY (`id`),
                              UNIQUE INDEX `name`(`name`) COMMENT '组名唯一索引'
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='Django用户组表';

-- ====================================================================================
-- 【表2】auth_group_permissions - 用户组与权限关联表（多对多）
-- 【功能】定义每个用户组拥有哪些权限，组内用户自动继承这些权限
-- ====================================================================================
DROP TABLE IF EXISTS `auth_group_permissions`;
CREATE TABLE `auth_group_permissions` (
                                          `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '关联ID，主键自增',
                                          `group_id` int(11) NOT NULL COMMENT '用户组ID，外键→auth_group.id',
                                          `permission_id` int(11) NOT NULL COMMENT '权限ID，外键→auth_permission.id',
                                          PRIMARY KEY (`id`),
                                          UNIQUE INDEX `auth_group_permissions_group_id_permission_id_0cd325b0_uniq`(`group_id`, `permission_id`),
                                          INDEX `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm`(`permission_id`),
                                          CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
                                          CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='用户组-权限关联表';

-- ====================================================================================
-- 【表3】auth_permission - 权限定义表
-- 【功能】存储系统所有权限，Django为每个模型自动生成add/change/delete/view四种权限
-- 【业务权限】rooms.room(房间)、customers.customer(客户)、reservations.reservation(预订)
--            finance.income(收入)、finance.expense(支出)、employees.employee(员工)
-- ====================================================================================
DROP TABLE IF EXISTS `auth_permission`;
CREATE TABLE `auth_permission` (
                                   `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '权限ID，主键自增',
                                   `name` varchar(255) NOT NULL COMMENT '权限显示名称，如"Can add room"',
                                   `content_type_id` int(11) NOT NULL COMMENT '内容类型ID，指明权限属于哪个模型',
                                   `codename` varchar(100) NOT NULL COMMENT '权限代码，如"add_room"，程序中用于判断',
                                   PRIMARY KEY (`id`),
                                   UNIQUE INDEX `auth_permission_content_type_id_codename_01ab375a_uniq`(`content_type_id`, `codename`),
                                   CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=49 DEFAULT CHARSET=utf8 COMMENT='Django权限定义表';

-- 【权限数据】ID 1-24为Django系统权限，ID 25-48为酒店业务权限
INSERT INTO `auth_permission` VALUES
                                  (1, 'Can add log entry', 1, 'add_logentry'),          -- 日志-添加
                                  (2, 'Can change log entry', 1, 'change_logentry'),    -- 日志-修改
                                  (3, 'Can delete log entry', 1, 'delete_logentry'),    -- 日志-删除
                                  (4, 'Can view log entry', 1, 'view_logentry'),        -- 日志-查看
                                  (5, 'Can add permission', 2, 'add_permission'),       -- 权限管理-添加
                                  (6, 'Can change permission', 2, 'change_permission'), -- 权限管理-修改
                                  (7, 'Can delete permission', 2, 'delete_permission'), -- 权限管理-删除
                                  (8, 'Can view permission', 2, 'view_permission'),     -- 权限管理-查看
                                  (9, 'Can add group', 3, 'add_group'),                 -- 用户组-添加
                                  (10, 'Can change group', 3, 'change_group'),          -- 用户组-修改
                                  (11, 'Can delete group', 3, 'delete_group'),          -- 用户组-删除
                                  (12, 'Can view group', 3, 'view_group'),              -- 用户组-查看
                                  (13, 'Can add user', 4, 'add_user'),                  -- 用户管理-添加
                                  (14, 'Can change user', 4, 'change_user'),            -- 用户管理-修改
                                  (15, 'Can delete user', 4, 'delete_user'),            -- 用户管理-删除
                                  (16, 'Can view user', 4, 'view_user'),                -- 用户管理-查看
                                  (17, 'Can add content type', 5, 'add_contenttype'),
                                  (18, 'Can change content type', 5, 'change_contenttype'),
                                  (19, 'Can delete content type', 5, 'delete_contenttype'),
                                  (20, 'Can view content type', 5, 'view_contenttype'),
                                  (21, 'Can add session', 6, 'add_session'),
                                  (22, 'Can change session', 6, 'change_session'),
                                  (23, 'Can delete session', 6, 'delete_session'),
                                  (24, 'Can view session', 6, 'view_session'),
                                  (25, 'Can add room', 7, 'add_room'),                  -- 【房间】添加新房间
                                  (26, 'Can change room', 7, 'change_room'),            -- 【房间】修改房间信息
                                  (27, 'Can delete room', 7, 'delete_room'),            -- 【房间】删除房间
                                  (28, 'Can view room', 7, 'view_room'),                -- 【房间】查看房间列表
                                  (29, 'Can add customer', 8, 'add_customer'),          -- 【客户】登记新客户
                                  (30, 'Can change customer', 8, 'change_customer'),    -- 【客户】修改客户信息
                                  (31, 'Can delete customer', 8, 'delete_customer'),    -- 【客户】删除客户
                                  (32, 'Can view customer', 8, 'view_customer'),        -- 【客户】查看客户列表
                                  (33, 'Can add reservation', 9, 'add_reservation'),    -- 【预订】创建新预订
                                  (34, 'Can change reservation', 9, 'change_reservation'), -- 【预订】修改预订(入住/离店/退订)
                                  (35, 'Can delete reservation', 9, 'delete_reservation'), -- 【预订】删除预订记录
                                  (36, 'Can view reservation', 9, 'view_reservation'),  -- 【预订】查看预订列表
                                  (37, 'Can add expense', 10, 'add_expense'),           -- 【支出】录入支出
                                  (38, 'Can change expense', 10, 'change_expense'),     -- 【支出】修改支出记录
                                  (39, 'Can delete expense', 10, 'delete_expense'),     -- 【支出】删除支出记录
                                  (40, 'Can view expense', 10, 'view_expense'),         -- 【支出】查看支出报表
                                  (41, 'Can add income', 11, 'add_income'),             -- 【收入】录入收入
                                  (42, 'Can change income', 11, 'change_income'),       -- 【收入】修改收入记录
                                  (43, 'Can delete income', 11, 'delete_income'),       -- 【收入】删除收入记录
                                  (44, 'Can view income', 11, 'view_income'),           -- 【收入】查看收入报表
                                  (45, 'Can add employee', 12, 'add_employee'),         -- 【员工】添加员工档案
                                  (46, 'Can change employee', 12, 'change_employee'),   -- 【员工】修改员工信息
                                  (47, 'Can delete employee', 12, 'delete_employee'),   -- 【员工】删除员工档案
                                  (48, 'Can view employee', 12, 'view_employee');       -- 【员工】查看员工列表

-- ====================================================================================
-- 【表4】auth_user - 系统用户表
-- 【功能】存储管理员和员工账户，用于登录系统（CustomLoginView使用此表验证）
-- 【密码】使用PBKDF2_SHA256算法加密，60万次迭代，安全可靠
-- ====================================================================================
DROP TABLE IF EXISTS `auth_user`;
CREATE TABLE `auth_user` (
                             `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '用户ID，主键自增',
                             `password` varchar(128) NOT NULL COMMENT '加密密码(PBKDF2_SHA256算法)',
                             `last_login` datetime(6) NULL COMMENT '最后登录时间',
                             `is_superuser` tinyint(1) NOT NULL COMMENT '是否超级管理员(1=是,拥有所有权限)',
                             `username` varchar(150) NOT NULL COMMENT '用户名，用于登录，必须唯一',
                             `first_name` varchar(150) NOT NULL COMMENT '名',
                             `last_name` varchar(150) NOT NULL COMMENT '姓',
                             `email` varchar(254) NOT NULL COMMENT '邮箱',
                             `is_staff` tinyint(1) NOT NULL COMMENT '是否可访问Admin后台(1=可以)',
                             `is_active` tinyint(1) NOT NULL COMMENT '账户是否激活(1=激活,0=禁用)',
                             `date_joined` datetime(6) NOT NULL COMMENT '账户创建时间',
                             PRIMARY KEY (`id`),
                             UNIQUE INDEX `username`(`username`) COMMENT '用户名唯一索引'
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8 COMMENT='Django用户表';

-- 【默认管理员账户】用户名:admin 密码:admin 权限:超级管理员
-- is_superuser=1 表示拥有所有权限，无需单独分配
-- is_staff=1 表示可以访问Django Admin管理后台
INSERT INTO `auth_user` VALUES (1, 'pbkdf2_sha256$600000$k3jggXPi7lWW586H7pIvSn$qM4sxEZEojXAUNcGETpU8jNKVrlH9xE/wWHuMYv/Eho=', '2025-12-13 10:48:42.000000', 1, 'admin', '', '', 'admin@hotel.com', 1, 1, '2025-11-05 08:17:17.712962');

-- ====================================================================================
-- 【表5-6】auth_user_groups / auth_user_user_permissions - 用户关联表
-- ====================================================================================
DROP TABLE IF EXISTS `auth_user_groups`;
CREATE TABLE `auth_user_groups` (
                                    `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '关联ID',
                                    `user_id` int(11) NOT NULL COMMENT '用户ID，外键→auth_user.id',
                                    `group_id` int(11) NOT NULL COMMENT '用户组ID，外键→auth_group.id',
                                    PRIMARY KEY (`id`),
                                    UNIQUE INDEX `auth_user_groups_user_id_group_id_94350c0c_uniq`(`user_id`, `group_id`),
                                    INDEX `auth_user_groups_group_id_97559544_fk_auth_group_id`(`group_id`),
                                    CONSTRAINT `auth_user_groups_group_id_97559544_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
                                    CONSTRAINT `auth_user_groups_user_id_6a12ed8b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='用户-用户组关联表';

DROP TABLE IF EXISTS `auth_user_user_permissions`;
CREATE TABLE `auth_user_user_permissions` (
                                              `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '关联ID',
                                              `user_id` int(11) NOT NULL COMMENT '用户ID，外键→auth_user.id',
                                              `permission_id` int(11) NOT NULL COMMENT '权限ID，外键→auth_permission.id',
                                              PRIMARY KEY (`id`),
                                              UNIQUE INDEX `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq`(`user_id`, `permission_id`),
                                              INDEX `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm`(`permission_id`),
                                              CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
                                              CONSTRAINT `auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='用户-权限直接关联表';

-- ====================================================================================
-- 【表7】django_content_type - 模型内容类型注册表
-- 【功能】Django自动维护，记录项目中所有模型，用于权限系统和日志关联
-- ====================================================================================
DROP TABLE IF EXISTS `django_content_type`;
CREATE TABLE `django_content_type` (
                                       `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '内容类型ID',
                                       `app_label` varchar(100) NOT NULL COMMENT '应用名称，如rooms、customers',
                                       `model` varchar(100) NOT NULL COMMENT '模型名称，如room、customer',
                                       PRIMARY KEY (`id`),
                                       UNIQUE INDEX `django_content_type_app_label_model_76bd3d3b_uniq`(`app_label`, `model`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8 COMMENT='Django内容类型表';

-- 【内容类型数据】记录项目所有模型
INSERT INTO `django_content_type` VALUES
                                      (1, 'admin', 'logentry'),           -- Django管理日志
                                      (2, 'auth', 'permission'),          -- 权限模型
                                      (3, 'auth', 'group'),               -- 用户组模型
                                      (4, 'auth', 'user'),                -- 用户模型
                                      (5, 'contenttypes', 'contenttype'), -- 内容类型模型
                                      (6, 'sessions', 'session'),         -- 会话模型
                                      (7, 'rooms', 'room'),               -- 【业务】房间模型 → rooms/models.py
                                      (8, 'customers', 'customer'),       -- 【业务】客户模型 → customers/models.py
                                      (9, 'reservations', 'reservation'), -- 【业务】预订模型 → reservations/models.py
                                      (10, 'finance', 'expense'),         -- 【业务】支出模型 → finance/models.py
                                      (11, 'finance', 'income'),          -- 【业务】收入模型 → finance/models.py
                                      (12, 'employees', 'employee');      -- 【业务】员工模型 → employees/models.py

-- ====================================================================================
-- 【表8】django_admin_log - 管理后台操作日志表
-- 【功能】自动记录Admin后台的所有增删改操作，用于审计追踪
-- 【显示】settings.py中SIMPLEUI_HOME_ACTION=True时在首页显示最近动作
-- ====================================================================================
DROP TABLE IF EXISTS `django_admin_log`;
CREATE TABLE `django_admin_log` (
                                    `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '日志ID',
                                    `action_time` datetime(6) NOT NULL COMMENT '操作时间',
                                    `object_id` longtext NULL COMMENT '被操作对象的ID',
                                    `object_repr` varchar(200) NOT NULL COMMENT '对象的字符串表示',
                                    `action_flag` smallint(5) UNSIGNED NOT NULL COMMENT '操作类型：1=新增,2=修改,3=删除',
                                    `change_message` longtext NOT NULL COMMENT '变更说明(JSON格式)',
                                    `content_type_id` int(11) NULL COMMENT '操作的模型类型ID',
                                    `user_id` int(11) NOT NULL COMMENT '执行操作的用户ID',
                                    PRIMARY KEY (`id`),
                                    INDEX `django_admin_log_content_type_id_c4bce8eb_fk_django_co`(`content_type_id`),
                                    INDEX `django_admin_log_user_id_c564eba6_fk_auth_user_id`(`user_id`),
                                    CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
                                    CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='Django管理后台操作日志';

-- ====================================================================================
-- 【表9】django_migrations - 数据库迁移记录表
-- 【功能】记录已执行的迁移文件，防止重复执行，是Django ORM的核心功能
-- ====================================================================================
DROP TABLE IF EXISTS `django_migrations`;
CREATE TABLE `django_migrations` (
                                     `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '迁移记录ID',
                                     `app` varchar(255) NOT NULL COMMENT '应用名称',
                                     `name` varchar(255) NOT NULL COMMENT '迁移文件名',
                                     `applied` datetime(6) NOT NULL COMMENT '迁移执行时间',
                                     PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=26 DEFAULT CHARSET=utf8 COMMENT='Django迁移记录表';

-- 【迁移记录】记录所有应用的迁移历史
INSERT INTO `django_migrations` VALUES
                                    (1, 'contenttypes', '0001_initial', '2025-11-02 08:16:31.090469'),
                                    (2, 'auth', '0001_initial', '2025-11-02 08:16:31.339696'),
                                    (3, 'admin', '0001_initial', '2025-11-02 08:16:31.402380'),
                                    (4, 'admin', '0002_logentry_remove_auto_add', '2025-11-02 08:16:31.407885'),
                                    (5, 'admin', '0003_logentry_add_action_flag_choices', '2025-11-02 08:16:31.413890'),
                                    (6, 'contenttypes', '0002_remove_content_type_name', '2025-11-02 08:16:31.445455'),
                                    (7, 'auth', '0002_alter_permission_name_max_length', '2025-11-02 08:16:31.473565'),
                                    (8, 'auth', '0003_alter_user_email_max_length', '2025-11-02 08:16:31.499422'),
                                    (9, 'auth', '0004_alter_user_username_opts', '2025-11-02 08:16:31.504424'),
                                    (10, 'auth', '0005_alter_user_last_login_null', '2025-11-02 08:16:31.528463'),
                                    (11, 'auth', '0006_require_contenttypes_0002', '2025-11-02 08:16:31.530462'),
                                    (12, 'auth', '0007_alter_validators_add_error_messages', '2025-11-02 08:16:31.535463'),
                                    (13, 'auth', '0008_alter_user_username_max_length', '2025-11-02 08:16:31.545520'),
                                    (14, 'auth', '0009_alter_user_last_name_max_length', '2025-11-02 08:16:31.557123'),
                                    (15, 'auth', '0010_alter_group_name_max_length', '2025-11-02 08:16:31.587202'),
                                    (16, 'auth', '0011_update_proxy_permissions', '2025-11-02 08:16:31.592744'),
                                    (17, 'auth', '0012_alter_user_first_name_max_length', '2025-11-02 08:16:31.599394'),
                                    (18, 'customers', '0001_initial', '2025-11-02 08:16:31.614651'),       -- 客户模型初始迁移
                                    (19, 'employees', '0001_initial', '2025-11-02 08:16:31.622375'),       -- 员工模型初始迁移
                                    (20, 'finance', '0001_initial', '2025-11-02 08:16:31.636470'),         -- 财务模型初始迁移
                                    (21, 'rooms', '0001_initial', '2025-11-02 08:16:31.647978'),           -- 房间模型初始迁移
                                    (22, 'reservations', '0001_initial', '2025-11-02 08:16:31.715863'),    -- 预订模型初始迁移
                                    (23, 'sessions', '0001_initial', '2025-11-02 08:16:31.733882'),
                                    (24, 'rooms', '0002_room_pictures', '2025-11-05 09:52:53.212047'),     -- 房间图片字段迁移
                                    (25, 'reservations', '0002_alter_reservation_status', '2025-11-08 16:06:33.279184');

-- ====================================================================================
-- 【表10】django_session - 用户会话存储表
-- 【功能】存储用户登录会话数据，实现"记住登录状态"功能
-- 【清理】过期会话可通过 python manage.py clearsessions 清理
-- ====================================================================================
DROP TABLE IF EXISTS `django_session`;
CREATE TABLE `django_session` (
                                  `session_key` varchar(40) NOT NULL COMMENT '会话密钥，主键',
                                  `session_data` longtext NOT NULL COMMENT '加密的会话数据(Base64编码)',
                                  `expire_date` datetime(6) NOT NULL COMMENT '会话过期时间',
                                  PRIMARY KEY (`session_key`),
                                  INDEX `django_session_expire_date_a5c62663`(`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='Django会话存储表';


-- ====================================================================================
-- 【表11】customers_customer - 客户信息表
-- 【功能】存储酒店客户的基本信息，办理入住时必须登记
-- 【对应模型】customers/models.py → Customer类
-- 【验证规则】身份证号18位(正则验证)，手机号11位(1开头)
-- 【关联】被reservations_reservation表引用，一个客户可有多个预订记录
-- ====================================================================================
DROP TABLE IF EXISTS `customers_customer`;
CREATE TABLE `customers_customer` (
                                      `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '客户ID，主键自增',
                                      `name` varchar(100) NOT NULL COMMENT '客户姓名，必填',
                                      `id_number` varchar(18) NOT NULL COMMENT '身份证号，18位，必须唯一，用于身份验证',
                                      `phone` varchar(15) NOT NULL COMMENT '手机号码，11位，1开头，用于联系客户',
                                      `email` varchar(254) NOT NULL COMMENT '电子邮箱，可用于发送预订确认',
                                      `address` longtext NOT NULL COMMENT '联系地址，可为空',
                                      PRIMARY KEY (`id`),
                                      UNIQUE INDEX `id_number`(`id_number`) COMMENT '身份证号唯一索引，防止重复登记'
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8 COMMENT='客户信息表';

-- 【客户数据】示例客户信息（已修正为合规的18位身份证号和11位手机号）
-- 身份证号格式：6位地区码 + 8位出生日期 + 3位顺序码 + 1位校验码
-- 手机号格式：1开头的11位数字
INSERT INTO `customers_customer` VALUES
                                     (1, '张亦涵', '640104200301150023', '13812345678', 'zhangyihan@email.com', '宁夏银川市兴庆区'),  -- 客户1：宁夏籍，2003年出生
                                     (2, '余瑞', '640104200205200035', '13987654321', 'yurui@email.com', '宁夏银川市西夏区'),        -- 客户2：宁夏籍，2002年出生
                                     (3, '李明', '110101199001011234', '15012345678', 'liming@email.com', '北京市东城区');           -- 客户3：北京籍，1990年出生


-- ====================================================================================
-- 【表12】employees_employee - 员工信息表
-- 【功能】存储酒店员工的档案信息，包括职位、薪资、入职日期等
-- 【对应模型】employees/models.py → Employee类
-- 【后台管理】settings.py中SIMPLEUI_CONFIG配置为"员工管理"菜单
-- 【状态说明】Active=在职，Inactive=离职
-- ====================================================================================
DROP TABLE IF EXISTS `employees_employee`;
CREATE TABLE `employees_employee` (
                                      `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '员工ID，主键自增',
                                      `name` varchar(100) NOT NULL COMMENT '员工姓名',
                                      `position` varchar(100) NOT NULL COMMENT '职位，如：前台、保洁、经理',
                                      `phone` varchar(15) NOT NULL COMMENT '联系电话，11位手机号',
                                      `email` varchar(254) NOT NULL COMMENT '工作邮箱',
                                      `address` longtext NOT NULL COMMENT '家庭住址',
                                      `salary` decimal(10,2) NOT NULL COMMENT '月薪，单位：元，保留2位小数',
                                      `hire_date` date NOT NULL COMMENT '入职日期',
                                      `status` varchar(20) NOT NULL COMMENT '在职状态：Active=在职，Inactive=离职',
                                      PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8 COMMENT='员工信息表';

-- 【员工数据】示例员工信息（已修正为合规的11位手机号）
INSERT INTO `employees_employee` VALUES
                                     (1, '江业平', '前台', '13611112222', 'jiangyeping@hotel.com', '宁夏银川市金凤区', 4500.00, '2025-11-01', 'Active'),  -- 前台，负责客户接待和预订办理
                                     (2, '张博宸', '经理', '13722223333', 'zhangbochen@hotel.com', '宁夏银川市兴庆区', 8000.00, '2025-10-15', 'Active'),  -- 经理，负责酒店整体运营
                                     (3, '王五', '保洁', '13833334444', 'wangayi@hotel.com', '宁夏银川市西夏区', 3500.00, '2025-11-01', 'Active');      -- 保洁，负责客房卫生


-- ====================================================================================
-- 【表13】rooms_room - 房间信息表
-- 【功能】存储酒店各房间的详细信息，是预订系统的核心数据
-- 【对应模型】rooms/models.py → Room类
-- 【房间类型】Single=单人间, Double=双人间, Suite=套房, Deluxe=豪华间
-- 【房间状态】Available=空闲, Booked=已预订, Occupied=已入住, Maintenance=维修中
-- 【图片存储】pictures字段存储相对路径，实际文件在media/pictures/目录
-- 【关联】被reservations_reservation表引用，房间状态由预订系统自动更新
-- ====================================================================================
DROP TABLE IF EXISTS `rooms_room`;
CREATE TABLE `rooms_room` (
                              `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '房间ID，主键自增',
                              `room_number` varchar(10) NOT NULL COMMENT '房间号，如101、202，格式：楼层号+房间序号，必须唯一',
                              `room_type` varchar(50) NOT NULL COMMENT '房间类型：Single=单人间,Double=双人间,Suite=套房,Deluxe=豪华间',
                              `price` decimal(10,2) NOT NULL COMMENT '每晚房价，单位：元，预订时自动计算总价',
                              `facilities` longtext NOT NULL COMMENT '房间设施描述，如：WiFi、电视、空调、浴缸等',
                              `status` varchar(20) NOT NULL COMMENT '房间状态：Available=空闲,Booked=已预订,Occupied=已入住,Maintenance=维修中',
                              `floor` int(11) NOT NULL COMMENT '所在楼层，用于房间分类显示',
                              `capacity` int(11) NOT NULL COMMENT '最大容纳人数，预订时会校验入住人数不能超过此值',
                              `description` longtext NOT NULL COMMENT '房间详细描述，可为空',
                              `pictures` varchar(100) NULL COMMENT '房间主图路径，存储在media/pictures/目录',
                              PRIMARY KEY (`id`),
                              UNIQUE INDEX `room_number`(`room_number`) COMMENT '房间号唯一索引'
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8 COMMENT='房间信息表';

-- 【房间数据】示例房间信息（已修正：单人间使用单人床，价格合理调整）
-- 价格计算：预订时 paid_amount = (离店日期 - 入住日期) × price
INSERT INTO `rooms_room` VALUES
                             (1, '201', 'Double', 198.00, 'WiFi、液晶电视、独立卫浴、热水器、空调、书桌、双人床', 'Available', 2, 2, '温馨双人间，适合情侣或朋友入住', 'pictures/201.jpg'),     -- 2楼双人间，198元/晚
                             (2, '302', 'Deluxe', 358.00, 'WiFi、液晶电视、独立卫浴、热水器、空调、书桌、豪华大床、浴缸、沙发、迷你吧', 'Available', 3, 2, '豪华套间，配备浴缸和迷你吧', 'pictures/302.jpg'),  -- 3楼豪华间，358元/晚
                             (3, '403', 'Single', 128.00, 'WiFi、液晶电视、独立卫浴、热水器、空调、单人床', 'Available', 4, 1, '经济单人间，适合商务出差', 'pictures/403.jpg');               -- 4楼单人间，128元/晚


-- ====================================================================================
-- 【表14】reservations_reservation - 预订记录表（核心业务表）
-- 【功能】存储客户的房间预订记录，管理预订全生命周期（预订→入住→离店/退订）
-- 【对应模型】reservations/models.py → Reservation类（包含复杂业务逻辑）
-- 【预订状态】Booked=已预定, CheckedIn=已入住, CheckedOut=已离店, Refunded=已退订
-- 【自动计算】paid_amount = (check_out_date - check_in_date) × room.price
-- 【房间联动】创建/修改预订时自动更新房间状态
-- 【财务联动】确认预订自动创建收入记录，退订自动创建退款支出记录
-- 【后台管理】settings.py中SIMPLEUI_CONFIG配置为"酒店管理-预订管理"菜单
-- ====================================================================================
DROP TABLE IF EXISTS `reservations_reservation`;
CREATE TABLE `reservations_reservation` (
                                            `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '预订ID，主键自增，即预订号',
                                            `check_in_date` date NOT NULL COMMENT '入住日期，必须早于离店日期',
                                            `check_out_date` date NOT NULL COMMENT '离店日期，必须晚于入住日期',
                                            `number_of_guests` int(11) NOT NULL COMMENT '入住人数，必须在1-100之间且不超过房间容量',
                                            `special_requests` longtext NOT NULL COMMENT '特殊要求，如：需要加床、安静房间等',
                                            `status` varchar(20) NOT NULL COMMENT '预订状态：Booked=已预定,CheckedIn=已入住,CheckedOut=已离店,Refunded=已退订',
                                            `paid_amount` decimal(10,2) NOT NULL DEFAULT 0.00 COMMENT '已付金额，自动计算=(离店-入住)天数×房价',
                                            `refund_amount` decimal(10,2) NOT NULL DEFAULT 0.00 COMMENT '退款金额，退订时全额退款',
                                            `income_recorded` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否已记录收入(1=是)，防止重复创建收入记录',
                                            `refund_recorded` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否已处理退款(1=是)，防止重复退款',
                                            `created_at` datetime(6) NOT NULL COMMENT '预订创建时间，自动设置',
                                            `updated_at` datetime(6) NOT NULL COMMENT '最后更新时间，自动更新',
                                            `customer_id` bigint(20) NOT NULL COMMENT '客户ID，外键→customers_customer.id',
                                            `room_id` bigint(20) NOT NULL COMMENT '房间ID，外键→rooms_room.id',
                                            PRIMARY KEY (`id`),
                                            INDEX `reservations_reserva_customer_id_9e54bd39_fk_customers`(`customer_id`) COMMENT '客户ID索引，加速按客户查询预订',
                                            INDEX `reservations_reservation_room_id_f7d9ba76_fk_rooms_room_id`(`room_id`) COMMENT '房间ID索引，加速按房间查询预订',
                                            CONSTRAINT `reservations_reserva_customer_id_9e54bd39_fk_customers` FOREIGN KEY (`customer_id`) REFERENCES `customers_customer` (`id`),
                                            CONSTRAINT `reservations_reservation_room_id_f7d9ba76_fk_rooms_room_id` FOREIGN KEY (`room_id`) REFERENCES `rooms_room` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COMMENT='预订记录表';

-- 【预订数据】初始为空，通过Admin后台创建预订
-- 预订流程：创建预订(Booked) → 办理入住(CheckedIn) → 办理离店(CheckedOut)
-- 退订流程：创建预订(Booked) → 取消预订(Refunded) → 自动全额退款


-- ====================================================================================
-- 【表15】finance_income - 收入记录表
-- 【功能】存储酒店的各类收入信息，预订确认时自动创建客房收入记录
-- 【对应模型】finance/models.py → Income类
-- 【收入来源】Room=客房收入(自动创建), Food=餐饮收入, Other=其他收入
-- 【自动创建】当预订状态确认且paid_amount>0时，自动创建收入记录
-- 【后台管理】settings.py中SIMPLEUI_CONFIG配置为"财务管理-收入管理"菜单
-- ====================================================================================
DROP TABLE IF EXISTS `finance_income`;
CREATE TABLE `finance_income` (
                                  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '收入记录ID，主键自增',
                                  `date` date NOT NULL COMMENT '收入日期',
                                  `amount` decimal(10,2) NOT NULL COMMENT '收入金额，单位：元',
                                  `source` varchar(50) NOT NULL COMMENT '收入来源：Room=客房,Food=餐饮,Other=其他',
                                  `description` longtext NOT NULL COMMENT '收入说明，客房收入会自动填充预订详情',
                                  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COMMENT='收入记录表';

-- 【收入数据】初始为空，预订确认时自动创建
-- 客房收入description格式：预订号:{id}|客户:{name}|房间:{room_number}|{check_in}至{check_out}({days}天)|人数:{guests}


-- ====================================================================================
-- 【表16】finance_expense - 支出记录表
-- 【功能】存储酒店的各类支出信息，退订时自动创建退款支出记录
-- 【对应模型】finance/models.py → Expense类
-- 【支出类别】Salary=工资, Maintenance=维修, Utilities=水电, Other=其他(含退款)
-- 【自动创建】当预订状态变为Refunded(已退订)时，自动创建退款支出记录
-- 【后台管理】settings.py中SIMPLEUI_CONFIG配置为"财务管理-支出管理"菜单
-- ====================================================================================
DROP TABLE IF EXISTS `finance_expense`;
CREATE TABLE `finance_expense` (
                                   `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '支出记录ID，主键自增',
                                   `date` date NOT NULL COMMENT '支出日期',
                                   `amount` decimal(10,2) NOT NULL COMMENT '支出金额，单位：元',
                                   `category` varchar(50) NOT NULL COMMENT '支出类别：Salary=工资,Maintenance=维修,Utilities=水电,Other=其他',
                                   `description` longtext NOT NULL COMMENT '支出说明，退款会自动填充预订详情',
                                   PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COMMENT='支出记录表';

-- 【支出数据】初始为空，退订或手动录入时创建
-- 退款支出description格式：退款-预订号:{id}|客户:{name}|房间:{room_number}|{check_in}至{check_out}({days}天)|退款:￥{amount}


-- ====================================================================================
-- 【结束设置】
-- 数据导入完成，重新启用外键约束检查
-- 这确保后续的数据操作都会进行外键完整性验证
-- ====================================================================================
SET FOREIGN_KEY_CHECKS = 1;