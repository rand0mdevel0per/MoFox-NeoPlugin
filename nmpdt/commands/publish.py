"""
publish.py - 发布插件到 registry

自动 fork registry 仓库、生成 entry 文件、commit、push 和创建 PR
"""

import json
import subprocess
import sys
import toml
from pathlib import Path


def publish_plugin(repo_url: str):
    """发布插件到 registry"""
    print("🚀 发布插件到 NeoPlugin Registry")
    print()

    # 1. 检查当前目录是否是插件目录
    manifest_path = Path("manifest.toml")
    if not manifest_path.exists():
        print("❌ 错误: 当前目录不是插件目录（找不到 manifest.toml）")
        sys.exit(1)

    # 2. 读取 manifest
    print("📋 读取插件信息...")
    try:
        manifest = toml.load(manifest_path)
        package = manifest.get("package", {})
        plugin_name = package.get("name", "")
        version = package.get("version", "")
        description = package.get("description", "")
        authors = package.get("authors", [])
        license_type = package.get("license", "")

        if not plugin_name:
            print("❌ 错误: manifest.toml 中缺少 package.name")
            sys.exit(1)

        print(f"  插件名: {plugin_name}")
        print(f"  版本: {version}")
        print()
    except Exception as e:
        print(f"❌ 错误: 无法解析 manifest.toml: {e}")
        sys.exit(1)

    # 3. Fork registry 仓库
    print("🔱 Fork registry 仓库...")
    registry_repo = "rand0mdevel0per/neoplugin-registry"

    try:
        result = subprocess.run(
            ["gh", "repo", "fork", registry_repo, "--clone=false"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            if "already exists" not in result.stderr:
                print(f"❌ Fork 失败: {result.stderr}")
                sys.exit(1)
        print("  ✅ Fork 成功")
    except FileNotFoundError:
        print("❌ 错误: 找不到 gh 命令，请先安装 GitHub CLI")
        sys.exit(1)

    print()

    # 4. Clone fork 的仓库
    print("📥 Clone registry 仓库...")
    import tempfile
    import shutil

    temp_dir = Path(tempfile.mkdtemp())
    registry_dir = temp_dir / "neoplugin-registry"

    try:
        # 获取当前用户名
        result = subprocess.run(
            ["gh", "api", "user", "-q", ".login"],
            capture_output=True,
            text=True
        )
        username = result.stdout.strip()

        # Clone fork
        fork_url = f"https://github.com/{username}/neoplugin-registry.git"
        subprocess.run(
            ["git", "clone", fork_url, str(registry_dir)],
            check=True,
            capture_output=True
        )
        print("  ✅ Clone 成功")
        print()
    except Exception as e:
        print(f"❌ Clone 失败: {e}")
        shutil.rmtree(temp_dir, ignore_errors=True)
        sys.exit(1)

    # 5. 生成 entry 文件
    print("📝 生成 entry 文件...")
    entry_data = {
        "name": plugin_name,
        "type": "lib" if manifest.get("package", {}).get("lib", False) else "plugin",
        "version": version,
        "versions": [version],
        "description": description,
        "author": authors[0] if authors else "",
        "repository": repo_url,
        "download_url": f"{repo_url}/archive/refs/heads/master.tar.gz",
        "checksum": "",
        "dependencies": manifest.get("dependencies", {}),
        "keywords": package.get("keywords", []),
        "license": license_type,
        "mofox_version": package.get("mofox_version", ">=2.0.0")
    }

    entry_file = registry_dir / "entries" / f"{plugin_name}.json"
    entry_file.parent.mkdir(parents=True, exist_ok=True)

    with open(entry_file, 'w', encoding='utf-8') as f:
        json.dump(entry_data, f, indent=2, ensure_ascii=False)

    print(f"  ✅ 已创建 entries/{plugin_name}.json")
    print()

    # 6. Commit 和 Push
    print("📤 提交并推送更改...")
    try:
        subprocess.run(
            ["git", "add", f"entries/{plugin_name}.json"],
            cwd=registry_dir,
            check=True
        )
        subprocess.run(
            ["git", "commit", "-m", f"feat: 添加插件 {plugin_name} v{version}"],
            cwd=registry_dir,
            check=True
        )
        subprocess.run(
            ["git", "push"],
            cwd=registry_dir,
            check=True
        )
        print("  ✅ 推送成功")
        print()
    except Exception as e:
        print(f"❌ 推送失败: {e}")
        shutil.rmtree(temp_dir, ignore_errors=True)
        sys.exit(1)

    # 7. 创建 PR
    print("🔀 创建 Pull Request...")
    try:
        result = subprocess.run(
            ["gh", "pr", "create",
             "--repo", registry_repo,
             "--title", f"feat: 添加插件 {plugin_name} v{version}",
             "--body", f"添加插件: {plugin_name}\n\n{description}"],
            cwd=registry_dir,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("  ✅ PR 创建成功")
            print(f"  {result.stdout.strip()}")
        else:
            print(f"  ⚠️  PR 创建失败: {result.stderr}")
    except Exception as e:
        print(f"❌ PR 创建失败: {e}")

    # 8. 清理
    shutil.rmtree(temp_dir, ignore_errors=True)

    print()
    print("🎉 发布完成！")

