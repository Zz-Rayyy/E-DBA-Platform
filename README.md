# E-DBA · Education Data Bay Area

Group C03 的软件工程课程项目。E-DBA 是一个基于 Flask 的多角色教育数据共享平台：组织管理员管理成员和服务，数据提供者配置课程与外部 API，数据消费者按权限访问课程、论文和学生信息服务。

> 这是课程演示项目。部分功能依赖外部论文、学生信息与银行接口；代码和数据流程未经生产环境安全审计。

## 项目功能

- **邮箱验证码登录与组织注册**：用户按角色登录；组织召集人提交注册申请和 PDF 证明文件。
- **两级注册审核**：E-Admin 初审，Senior E-Admin 终审；终审通过后创建组织和 O-Convener 账号。
- **组织与成员管理**：设置 DataUser 权限等级、服务开放范围、组织银行账户及会员费。
- **数据共享**：发布课程信息，配置论文、学生身份认证和 GPA 查询的外部 API。
- **日志与政策**：平台管理员管理政策并查看全平台日志；组织召集人查看本组织日志。

## 角色与权限

| 角色 | 主要功能 |
| --- | --- |
| **T-Admin** | 创建、编辑和删除 E-Admin / Senior E-Admin 账号；查看并回答用户求助问题。 |
| **E-Admin** | 初审组织注册申请；上传和管理平台政策；设置平台银行账户与各级会员费；筛选全平台日志。 |
| **Senior E-Admin** | 对初审通过的注册申请进行终审；通过后创建组织和 O-Convener。 |
| **O-Convener** | 管理本组织成员及权限，可通过 Excel 批量添加；启用服务并设置开放范围；维护组织银行账户、支付会员费、查看本组织日志。 |
| **DataUser Level 1** | 浏览政策、提交求助、查看课程信息、检索论文并下载 PDF。 |
| **DataUser Level 2** | 拥有 Level 1 功能，并可进行学生身份认证与 GPA 查询，支持 Excel 批量查询。 |
| **DataUser Level 3 / Data Provider** | 拥有 Level 1/2 功能，并可维护课程信息、配置外部服务 API。 |

### 登录与注册

登录和注册使用邮箱验证码。O-Convener 注册时提交组织信息和 PDF 证明文件。

![邮箱验证码登录页面](docs/screenshots/login.png)

### 平台管理员

T-Admin 管理管理员账号并处理用户问题。E-Admin 审核注册申请、设置会员费和平台账户、管理政策及查看日志。Senior E-Admin 负责终审。

![T-Admin 管理页面](docs/screenshots/t-admin.png)
![E-Admin 审核与配置页面](docs/screenshots/e-admin.png)
![E-Admin 政策与日志页面](docs/screenshots/e-admin-policy-logs.png)
![Senior E-Admin 终审页面](docs/screenshots/senior-e-admin.png)

### 组织召集人（O-Convener）

O-Convener 在组织工作台管理成员、服务和权限等级，也可以查看会员费支付摘要与组织日志。

![O-Convener 成员和服务管理](docs/screenshots/o-convener.png)
![O-Convener 银行账户和会员费](docs/screenshots/o-convener-payment.png)

### 数据提供者与消费者

Level 3 Data Provider 维护课程并配置服务 API。Level 1 DataUser 使用课程与论文等公开服务；Level 2 还可以进行学生身份认证和 GPA 查询。

![Data Provider 课程管理](docs/screenshots/data-provider-courses.png)
![Data Provider 服务 API 配置](docs/screenshots/data-provider-api.png)
![DataUser Level 1 工作台](docs/screenshots/data-consumer-level1.png)
![DataUser Level 2 工作台](docs/screenshots/data-consumer-level2.png)

以上界面截图提取自课程演示文稿第 19–33 页。

## 技术栈与结构

- Python、Flask、Flask-SQLAlchemy、PyMySQL、MySQL
- HTML、Bootstrap、原生 JavaScript；部分批量功能使用 pandas / openpyxl
- Flask Blueprint 按业务模块组织路由

```text
app/
├── models/       # 用户、组织、注册、服务、课程、账单、日志等数据模型
├── views/        # 各角色页面与业务接口
├── templates/    # 工作台页面
└── config/       # 数据库配置
teamwork.py       # Flask 入口
```

## 本地运行

需要 Python 3.10+ 和 MySQL。下面以 macOS / Linux shell 为例：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

编辑 `.env`，填入自己的 `DATABASE_URL`、`FLASK_SECRET_KEY`、`SMTP_EMAIL`、`SMTP_PASSWORD` 和 `SENIOR_ADMIN_EMAIL`。邮件密码应为邮箱服务商的 SMTP 授权码。`.env` 已被 Git 忽略。

在 MySQL 中创建数据库：

```sql
CREATE DATABASE IF NOT EXISTS `E-DBA`
DEFAULT CHARACTER SET utf8mb4
DEFAULT COLLATE utf8mb4_unicode_ci;
```

加载环境变量并启动：

```bash
set -a
source .env
set +a
python teamwork.py
```

打开 <http://127.0.0.1:5000/user/login>。首次启动会自动建表，但不会创建初始 T-Admin；初始化步骤及各业务流程见[项目使用文档](项目使用文档.md)。

## 演示范围与已知限制

- 论文检索与下载、学生身份认证、GPA 查询需要先配置可用的外部 API。
- 会员费支付调用课程环境中的外部银行转账接口，脱离该环境可能无法完成支付。
- 验证码仅保存在进程内存中，重启服务后失效。
- DataUser 的组织列表目前只返回其所属组织；跨组织搜索尚未完整实现。
- 求助问题与回复共用一个字段，回复后原问题正文会被覆盖；操作日志也尚未覆盖所有功能。

项目面向课程展示，不建议直接部署到公网。更完整的环境配置、数据模型和接口说明见[项目使用文档](项目使用文档.md)。
