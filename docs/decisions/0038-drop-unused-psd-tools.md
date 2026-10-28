# ADR-0038：移除未使用的 psd-tools，保留 Python 3.9 兼容性

日期：2026-10-28

## 背景

上游 PR #160 建议将 psd-tools 1.10.2 升级到 1.17.4，以覆盖 GHSA-2rmg-vrx8-9j2f 和 GHSA-8q6g-vjhf-jp8m。但 1.17.4 的 Python 要求为 >=3.10，与本项目仍测试 Python 3.9 的支持范围冲突。

## 决策

移除 requirements.txt 中的 psd-tools。仓库不存在对此库的导入；PSD 导出通过 `app.services.psd_writer` 的纯 Python 写入器和 Pillow 实现。用现有 PSD 写入/导出回归验证移除后行为。

不通过环境标记为 Python 3.9 保留有漏洞的旧版本，也不为一个未用到的依赖提高整个项目的运行时门槛。已有部署需从虚拟环境显式卸载 psd-tools，单纯重新安装 requirements 不会移除旧包。

## 依据

- [上游 PR #160](https://github.com/Hector-xue/IvyeaOps/pull/160)
- [psd-tools 1.17.4 Python 版本要求](https://pypi.org/project/psd-tools/1.17.4/)
- [智能对象路径读写公告](https://github.com/advisories/GHSA-2rmg-vrx8-9j2f)
- [异常内存分配公告](https://github.com/advisories/GHSA-8q6g-vjhf-jp8m)
