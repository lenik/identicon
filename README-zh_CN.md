# identicon

`identicon` 根据标识符生成确定性的方形头像。  
同一 ID（以及可选的盐）总会得到同一张图。

```bash
identicon [选项]... ID
```

ID 与盐按 UTF-8 编码。未指定 `--salt` 时，摘要为标识符的 SHA-256；指定盐时，摘要为以盐为密钥的 HMAC-SHA-256。

默认在标准输出写出 256×256 的 PNG。

### 选项

- `-s`, `--salt SALT` — 将盐混入哈希
- `-o`, `--out FILE` — 写入 FILE（格式由扩展名推断；默认标准输出）
- `-t`, `--type TYPE` — 头像风格：
  - `identicon` — 万花筒像素图案（默认）
  - `wavatar` — 表情与背景色各异的卡通小脸
  - `monsterid` — 长相独特的彩色像素小怪物
  - `retro` — 红白机时代的 8-bit 复古像素人脸
  - `robo` — 超萌小机器人
  - `1` / `set1` — Robohash 经典机器人
  - `2` / `set2` — Robohash 怪物
  - `3` / `set3` — Robohash 机器人头像
  - `4` / `set4` — Robohash 猫
  - `5` / `set5` — Robohash 人类头像
  - `6` / `set6` — Robohash 宇宙猿
- `-F`, `--format FMT` — `png`、`jpg`、`gif`、`bmp` 等
- `-S`, `--size PIXELS` — 边长像素（默认 256）
- `-b`, `--backcolor COLOR` — `red`、`#f00`、`#ff0000`，或 `rgb()` / `hsl()` / `rgba()` / `hsla()`
- `-f`, `--force` — 覆盖已存在的 FILE
- `-v`, `--verbose` / `-q`, `--quiet` / `-h`, `--help` / `--version`

### 示例

```bash
identicon alice@example.com >alice.png
identicon -t retro -S 128 -o face.png -f bob
identicon -s office -t robo -F jpg -o bot.jpg team-42
identicon -t set4 -S 128 -o cat.png user@host
```

## 仓库结构

- `src/` - Python 源码（`identicon.py`、`styles.py`、`runtime.py`）
- `third_party/robohash/` - 内嵌的 Robohash 拼装器与素材
- `tests/` - Python 单元测试（`unittest`）
- `debian/` - Debian 打包元数据
- `po/` - gettext 翻译目录
- `man/` - AsciiDoc man 页源文件（`man/*.adoc`）
- `meson.build` - 安装、测试与辅助目标

## 构建与测试

### 构建依赖（Debian 示例）

```bash
sudo apt install meson ninja-build python3 python3-pil gettext asciidoctor
```

### 配置并构建

使用绝对构建目录 `/build`：

```bash
meson setup /build
ninja -C /build
```

### 运行测试

```bash
meson test -C /build
```

Meson 通过 `python3 -m unittest discover` 执行 `tests/test_*.py`。

## i18n（gettext）

`identicon` 使用 `po/` 下的 gettext 翻译文件（`*.po` 与生成的 `.mo` 文件）。

Identicon 风格建议 `po/LINGUAS` 至少包含：**ar bn de es fr hi id it ja ko pt ru sv
ta te th tr ur vi zh_CN zh_TW**（英文为 msgid 源语言；`zh-cn`/`zh-tw` 对应
`zh_CN`/`zh_TW`）。

- 安装后运行时从系统 locale 目录加载翻译。
- 开发态运行（`/build/identicon`）若存在 `/build/po`，会优先使用项目内翻译资源。

### 同步翻译词条

使用 `posync` 从当前源码字符串同步词条：

```bash
ninja -C /build posync
```

`posync` 会：

- 为 `po/LINGUAS` 中每种语言补齐缺失消息
- 移除源码中已不再使用的废弃消息

### 构建翻译文件

```bash
ninja -C /build
```

### 快速测试语言

建议优先使用 `LANGUAGE=<lang>`，在开发环境中选择更稳定：

```bash
LANGUAGE=ja /build/identicon -h
LANGUAGE=zh_CN /build/identicon -h
```

`LANG=<lang>.<encoding>` 是否生效取决于系统是否已生成对应 locale。

## 安装 / 符号链接辅助命令

常规安装：

```bash
meson install -C /build
```

调试符号链接工作流（在已配置的安装前缀下）：

```bash
ninja -C /build install-symlinks
ninja -C /build uninstall-symlinks
```

## Debian 打包

```bash
dpkg-buildpackage -us -uc
```

## 许可证

Copyright (C) 2026 Lenik <identicon@bodz.net>

采用 **AGPL-3.0-or-later** 许可。  
本项目明确反对 AI 剥削与 AI 霸权，反对无脑 MIT 式许可证和政治愚蠢的 BSD 式许可证。  
完整文本及项目补充条款见 `LICENSE`。
