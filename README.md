# Clash Color Icons

适用于 Clash Verge Rev / Mihomo 策略组的彩色透明 SVG 图标库。图标直接存放在 `icons/`，无需网页项目、构建工具或运行服务。

## 快速使用

当前仓库使用 `Flytac/clash-icons`。如果你 Fork 到自己的 GitHub 账号，把 URL 中的 `Flytac` 和 `clash-icons` 分别替换成自己的 `USERNAME` 和 `REPOSITORY`。目录分为 `brands`、`regions` 和 `general`。

**Docker：** [`icons/brands/docker.svg`](icons/brands/docker.svg)

```text
https://fastly.jsdelivr.net/gh/Flytac/clash-icons@main/icons/brands/docker.svg
```

**Steam：** [`icons/brands/steam.svg`](icons/brands/steam.svg)

```text
https://fastly.jsdelivr.net/gh/Flytac/clash-icons@main/icons/brands/steam.svg
```

**日本：** [`icons/regions/japan.svg`](icons/regions/japan.svg)

```text
https://fastly.jsdelivr.net/gh/Flytac/clash-icons@main/icons/regions/japan.svg
```

**直连：** [`icons/general/direct.svg`](icons/general/direct.svg)

```text
https://fastly.jsdelivr.net/gh/Flytac/clash-icons@main/icons/general/direct.svg
```

Clash/Mihomo 策略组示例：

```yaml
- name: Docker
  type: select
  include-all-proxies: true
  icon: https://fastly.jsdelivr.net/gh/Flytac/clash-icons@main/icons/brands/docker.svg
  proxies:
    - DIRECT
```

`icons.md` 是完整可复制 URL 清单；`examples/clash-icons.yaml` 是名称到 `icon` URL 的片段，并非可独立运行的完整 Clash 配置。更改图标 URL 后，在 Clash Verge Rev 刷新配置或订阅以重新加载图标。CDN 可能缓存 `@main` 的旧内容；需要固定不变的版本时可改用 `@<commit SHA>`。

## 图标目录

| 类别 | 路径 | 内容 |
| --- | --- | --- |
| 品牌与服务 | [`icons/brands/`](icons/brands/) | Docker、Steam、Google、OpenAI 等 |
| 国家与地区 | [`icons/regions/`](icons/regions/) | 统一风格的圆形旗帜 |
| 通用策略组 | [`icons/general/`](icons/general/) | 代理、直连、自动选择、下载等 |

部分上游品牌色本身是黑色，例如 GitHub 和 Steam；这类黑色是上游记录的品牌色，不是未着色占位图。多色图标保留原有配色。`chatgpt.svg` 使用 OpenAI 公司标志代用，见 [`SOURCES.md`](SOURCES.md)。未找到合适开放来源的项目列在 [`missing-icons.md`](missing-icons.md)。

## 更新图标

编辑 [`scripts/icons.json`](scripts/icons.json) 增删图标。生成器只依赖 Python 3.10+ 标准库：

```sh
python scripts/generate_icons.py --owner USERNAME --repo REPOSITORY
```

脚本下载 Simple Icons 固定版本的 SVG 与品牌色、Tabler 通用图标、圆形旗帜和少数 Iconify 备用图标；设置确定的颜色，移除根元素固定宽高，保留 `viewBox`；同时重建 `icons.md`、`examples/clash-icons.yaml`、`SOURCES.md` 和 `missing-icons.md`。网络失败会逐项列出，已有图标不会因失败被删除。`.github/workflows/update-icons.yml` 支持手动触发并提交更新，不设定每日定时任务。

## 来源与许可

每个图标对应的上游地址、颜色与许可见 [`SOURCES.md`](SOURCES.md)，许可说明见 [`LICENSES.md`](LICENSES.md)。品牌标志及商标可能仍受其权利人约束；本仓库用于个人 Clash 配置展示。
