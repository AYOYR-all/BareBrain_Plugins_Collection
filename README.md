# BareBrain 插件集合

这个仓库是 BareBrain 的云端插件索引仓库，定位类似 `AstrBotDevs/AstrBot_Plugins_Collection`。

它不提供网页界面，只提供给 BareBrain Manager 读取的数据：

- `plugins.json`：插件市场索引。
- `plugin_cache.json`：插件缓存信息，后续可由 CI 自动生成。
- `validate_plugins.py`：插件索引校验脚本。
- `schemas/`：插件索引 JSON Schema。

## 和 BareBrain Manager 的关系

```text
BareBrain_Plugins_Collection
  -> 提供 plugins.json
  -> BareBrain Manager 本地读取并展示插件
  -> 用户选择插件和引脚
  -> Manager 生成 firmware_profile.json
  -> 提交到 GitHub Actions / 云构建服务
  -> 本地下载 artifact 并烧录
```

也就是说，GitHub 上放的是插件索引、插件源码地址和构建入口；真正的 UI 在本地端 `BareBrain-Manager`。

## 内置插件和市场插件

BareBrain 主仓库 `main/mods` 里的功能是内置插件，不需要登记在这里，也不需要一个插件一个仓库。

这个集合仓库只登记后续额外安装的市场插件。建议每个市场插件使用一个独立 GitHub 仓库，例如：

```text
barebrain-mod-weather
barebrain-mod-led-strip
barebrain-data-daily-briefing
```

每个插件仓库都应该提供 `barebrain.mod.json`，并在发布 release 后把 archive URL 和 checksum 写入 `plugins.json`。

## GitHub Actions 构建

构建可以放在 BareBrain 主仓库，也可以单独建一个 `BareBrain-Cloud-Build` 仓库。它的职责是：

1. 接收 Manager 生成的 `firmware_profile.json`。
2. 拉取 BareBrain 主仓库。
3. 拉取 `plugins.json` 中声明的市场插件。
4. 生成固件构建配置。
5. 编译 ESP32-S3 固件。
6. 上传 artifact 给本地 Manager 下载烧录。

## 校验

```powershell
python validate_plugins.py plugins.json
```

## 插件条目要求

每个插件条目至少要包含：

- `id`
- `name`
- `version`
- `type`
- `repo`
- `archive`
- `checksum`
- `targets`
- `permissions`
- `resources`

硬件相关插件必须声明 GPIO、UART、SPI、I2C 等资源，方便 Manager 在本地提前发现引脚冲突。
# Release workflow

Plugin archives must expose `barebrain.mod.json`, `CMakeLists.txt`, and `src/` at the ZIP root.

Create local deterministic archives and print their checksums:

```powershell
python package_plugins.py ..\barebrain-mod-display ..\barebrain-mod-tts --output-dir releases
```

After publishing the same archives as GitHub Release assets, update `plugins.json`, then run:

```powershell
python validate_plugins.py
python build_cache.py
```

The validator rejects placeholder or incomplete SHA-256 values.
