# NeoPlugin 一键安装脚本
# 用法: iwr -useb "https://raw.githubusercontent.com/rand0mdevel0per/NeoPlugin/master/install-neoplugin.ps1" | iex

Write-Host "🚀 NeoPlugin 一键安装脚本" -ForegroundColor Cyan
Write-Host ""

# 检查是否在 MoFox 目录
$currentDir = Get-Location
$botPyPath = Join-Path $currentDir "bot.py"

if (-not (Test-Path $botPyPath)) {
    Write-Host "❌ 错误: 当前目录不是 MoFox 根目录" -ForegroundColor Red
    Write-Host ""
    Write-Host "请先安装 MoFox，或切换到 MoFox 根目录后再运行此脚本。" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "快速安装 MoFox:" -ForegroundColor Green
    Write-Host "Set-ExecutionPolicy Bypass -Scope Process -Force; iwr -useb 'https://hk.gh-proxy.org/https://github.com/rand0mdevel0per/acscripts/raw/refs/heads/main/mofox-qsetup.ps1' | iex" -ForegroundColor Gray
    exit 1
}

Write-Host "✅ 检测到 MoFox 目录: $currentDir" -ForegroundColor Green
Write-Host ""

# 检查是否已安装 NeoPlugin
$loaderPath = Join-Path $currentDir "plugins\nmfpm_loader"
if (Test-Path $loaderPath) {
    Write-Host "⚠️  NeoPlugin 已安装" -ForegroundColor Yellow
    $response = Read-Host "是否重新安装? (y/N)"
    if ($response -ne "y" -and $response -ne "Y") {
        Write-Host "取消安装" -ForegroundColor Gray
        exit 0
    }
}

Write-Host "📥 正在下载 NeoPlugin..." -ForegroundColor Cyan

# 创建临时目录
$tempDir = Join-Path $env:TEMP "neoplugin-install-$(Get-Random)"
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

try {
    # 下载仓库（使用代理加速）
    $repoUrl = "https://hk.gh-proxy.org/https://github.com/rand0mdevel0per/NeoPlugin/archive/refs/heads/master.zip"
    $zipPath = Join-Path $tempDir "neoplugin.zip"

    Write-Host "  下载地址: $repoUrl" -ForegroundColor Gray
    Invoke-WebRequest -Uri $repoUrl -OutFile $zipPath -UseBasicParsing

    Write-Host "✅ 下载完成" -ForegroundColor Green
    Write-Host ""

    # 解压
    Write-Host "📦 正在解压..." -ForegroundColor Cyan
    Expand-Archive -Path $zipPath -DestinationPath $tempDir -Force

    $extractedDir = Join-Path $tempDir "NeoPlugin-master"

    if (-not (Test-Path $extractedDir)) {
        throw "解压失败: 找不到解压目录"
    }

    Write-Host "✅ 解压完成" -ForegroundColor Green
    Write-Host ""

    # 运行安装脚本
    Write-Host "🔧 正在安装 NeoPlugin..." -ForegroundColor Cyan
    $installScript = Join-Path $extractedDir "install.py"

    if (-not (Test-Path $installScript)) {
        throw "找不到 install.py"
    }

    # 运行 Python 安装脚本
    $pythonCmd = "python"
    if (Get-Command "python3" -ErrorAction SilentlyContinue) {
        $pythonCmd = "python3"
    }

    & $pythonCmd $installScript --mofox-path $currentDir

    if ($LASTEXITCODE -ne 0) {
        throw "安装失败"
    }

    Write-Host ""
    Write-Host "=" * 60 -ForegroundColor Green
    Write-Host "🎉 NeoPlugin 安装完成！" -ForegroundColor Green
    Write-Host "=" * 60 -ForegroundColor Green
    Write-Host ""
    Write-Host "📝 下一步:" -ForegroundColor Cyan
    Write-Host "  1. 同步插件仓库:" -ForegroundColor White
    Write-Host "     python scripts\nmfpm.py -Sy" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  2. 搜索插件:" -ForegroundColor White
    Write-Host "     python scripts\nmfpm.py -Ss <关键词>" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  3. 安装插件:" -ForegroundColor White
    Write-Host "     python scripts\nmfpm.py -S <插件名>" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  4. 启动 MoFox:" -ForegroundColor White
    Write-Host "     python bot.py" -ForegroundColor Gray
    Write-Host ""

} catch {
    Write-Host ""
    Write-Host "❌ 安装失败: $_" -ForegroundColor Red
    exit 1
} finally {
    # 清理临时文件
    if (Test-Path $tempDir) {
        Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}

