"""
publish.py - 发布插件到 registry

自动 fork registry 仓库、生成 entry 文件、commit、push 和创建 PR
"""

import json
import subprocess
import sys
import toml
from pathlib import Path


def _detect_or_create_repo() -> str:
    """
    检测或创建 git 仓库

    1. 检查是否有 git origin
    2. 如果有，返回 origin URL
    3. 如果没有，询问用户是否创建新仓库

    Returns:
        仓库 URL，如果失败返回 None
    """
    # 检查是否是 git 仓库
    if not Path(".git").exists():
        print("⚠️  当前目录不是 git 仓库")
        print()

        # 询问是否初始化 git 仓库
        response = input("是否初始化 git 仓库？(y/n): ").strip().lower()
        if response != 'y':
            return None

        # 初始化 git 仓库
        try:
            subprocess.run(["git", "init"], check=True, capture_output=True)
            subprocess.run(["git", "add", "."], check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", "Initial commit"], check=True, capture_output=True)
            print("✅ Git 仓库已初始化")
            print()
        except Exception as e:
            print(f"❌ 初始化 git 仓库失败: {e}")
            return None

    # 检查是否有 origin
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True
        )
        origin_url = result.stdout.strip()
        print(f"✅ 检测到 git origin: {origin_url}")
        print()
        return origin_url
    except subprocess.CalledProcessError:
        # 没有 origin，询问是否创建新仓库
        print("⚠️  未检测到 git origin")
        print()

        response = input("是否使用 gh CLI 创建新仓库？(y/n): ").strip().lower()
        if response != 'y':
            return None

        # 读取插件名称
        try:
            manifest = toml.load("manifest.toml")
            plugin_name = manifest.get("package", {}).get("name", "")
            if not plugin_name:
                print("❌ 无法从 manifest.toml 读取插件名称")
                return None
        except Exception as e:
            print(f"❌ 读取 manifest.toml 失败: {e}")
            return None

        # 使用 gh CLI 创建仓库
        try:
            print(f"正在创建仓库: {plugin_name}...")
            result = subprocess.run(
                ["gh", "repo", "create", plugin_name, "--public", "--source=.", "--remote=origin"],
                capture_output=True,
                text=True,
                check=True
            )
            print("✅ 仓库创建成功")

            # 推送到远程
            subprocess.run(["git", "push", "-u", "origin", "master"], check=True, capture_output=True)
            print("✅ 代码已推送到远程")
            print()

            # 获取仓库 URL
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except FileNotFoundError:
            print("❌ 错误: 找不到 gh 命令，请先安装 GitHub CLI")
            return None
        except Exception as e:
            print(f"❌ 创建仓库失败: {e}")
            return None


def publish_plugin(repo_url: str = None):
    """发布插件到 registry"""
    print("🚀 发布插件到 NeoPlugin Registry")
    print()

    # 1. 检查当前目录是否是插件目录
    manifest_path = Path("manifest.toml")
    if not manifest_path.exists():
        print("❌ 错误: 当前目录不是插件目录（找不到 manifest.toml）")
        sys.exit(1)

    # 1.5. 自动检测或创建 git 仓库
    if not repo_url:
        repo_url = _detect_or_create_repo()
        if not repo_url:
            print("❌ 错误: 无法获取仓库 URL")
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
        "checksum": "",
        "dependencies": manifest.get("dependencies", {}),
        "keywords": package.get("keywords", []),
        "license": license_type,
        "mofox_version": package.get("mofox_version", ">=0.10.0")
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

