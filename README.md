# 🛒 MartRetailTranPOS

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/framework-PyQt5-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-active-brightgreen.svg)]()

**MartRetailTranPOS** 是一款专为中小型超市和零售店打造的、基于 Python 和 PyQt5 的现代化进销存管理系统。系统集成了前台收银（POS）、库存管理、采购管理、会员管理及财务统计等核心功能，旨在为商家提供高效、稳定、易用的全流程数字化管理解决方案。

---

## 🌟 核心功能

### 💰 前台收银 (POS)
- **极速收银**: 支持条码扫描枪，支持手动快速搜索商品。
- **交易管理**: 支持挂单/取单、退货、作废订单。
- **灵活支付**: 支持现金、微信、支付宝、银行卡等多种支付方式。
- **小票打印**: 自动打印消费小票，支持 ESC/POS 指令集。

### 📦 商品与库存
- **商品维护**: 完整的商品属性管理（编码、条码、规格、多级价格等）。
- **实时库存**: 自动增减库存，支持多仓库管理。
- **智能预警**: 库存不足或过剩时自动提醒。
- **库存盘点**: 盈亏调整，确保账实相符。

### 🤝 采购与供应商
- **采购流程**: 从订单生成到验收转入库的全生命周期追踪。
- **供应商管理**: 详细的供应商资料及采购历史。

### 👥 会员管理
- **等级与积分**: 支持会员等级设定、消费积分累计与兑换。
- **充值管理**: 会员余额充值与消费扣款。

### 📊 报表与统计
- **销售报表**: 按日、周、月统计销售毛利。
- **财务流水**: 清晰的收支记录与供应商结算单。

---

## 🚀 快速开始

### 环境要求
- Windows 7/10/11 (推荐 64位)
- Python 3.8 或更高版本

### 安装步骤

1. **克隆项目**
   ```bash
   git clone https://github.com/your-repo/MartRetailTranPOS.git
   cd MartRetailTranPOS
   ```

2. **创建并激活虚拟环境**
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **初始化数据** (可选，用于测试)
   ```bash
   python scripts/fill_sample_data.py
   ```

5. **运行程序**
   ```bash
   python run.py
   ```

---

## 🔑 默认登录账户 (示例数据)

| 角色 | 用户名 | 密码 |
| :--- | :--- | :--- |
| **管理员** | `admin` | `admin123` |
| **收银员** | `cashier1` | `cashier123` |
| **经理** | `manager` | `manager123` |

---

## 🛠️ 技术架构

### 技术选型
- **UI 框架**: PyQt5 - 提供强大的跨平台桌面端交互体验。
- **数据库**: SQLAlchemy (ORM) - 支持 SQLite (单机) 及 PostgreSQL/MySQL (网络并发)。
- **报表导出**: Openpyxl & Pandas - 支持高性能数据导出。
- **打印系统**: PyWin32 & Python-Escpos - 兼容各种型号的小票打印机。

### 目录结构
```text
MartRetailTranPOS/
├── core/               # 核心框架（数据库、事件总线、日志）
├── modules/            # 功能模块（POS、商品、库存等）
│   ├── pos/            # 独立可插拔收银模块
│   └── ...             # 其他功能模块
├── shared/             # 共享组件（公共模型、工具类）
├── resources/          # 全局静态资源（图标、QSS样式）
├── scripts/            # 维护脚本（数据初始化、数据库迁移）
├── data/               # 本地存储（SQLite 数据库文件）
└── run.py              # 系统主入口
```

---

## 📋 开发计划 (Roadmap)

- [x] 核心框架搭建与模块化加载机制
- [x] 基础商品管理与分类系统
- [x] POS 核心收银流程实现
- [x] 采购与库存变动逻辑
- [x] 会员积分与余额系统
- [ ] 移动端支付深度集成 (支付插件)
- [ ] 数据可视化看板 (Dashboard)
- [ ] 自动升级服务

---

## 📄 开源协议

本项目基于 **Apache License** 协议开源。详情请参阅 [LICENSE](LICENSE) 文件。

---

## 📧 联系与支持

如有任何疑问或建议，请提交 [Issue](https://github.com/kuai410022283/MartRetailTranPOS/issues) 或联系开发团队。

- **捐赠** 如果觉得项目对你有用，可以捐赠任意资金，捐赠的资金，会用来维护项目及开发成本。

![捐赠二维码](捐赠二维码.jpg)

