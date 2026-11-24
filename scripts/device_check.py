#!/usr/bin/env python3
"""
双机环境自检：确认当前机器用哪个 device、装了什么、能不能跑训练。

不装 torch 也能跑（会报告缺失并给出安装命令）。
零第三方依赖，Python 3.8+，macOS / Windows 通用。

用法：
    python3 scripts/device_check.py
"""
import importlib.util
import os
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def info(label, value):
    print(f"  {label:<18} {value}")


def main():
    print("=" * 56)
    print("  双机环境自检 · AI 硕士自学 30 周计划")
    print("=" * 56)

    print("\n[系统信息]")
    info("系统", platform.platform())
    info("架构", platform.machine())
    info("Python", platform.python_version())
    info("CPU", platform.processor() or "未知")
    info("逻辑核心", os.cpu_count() or "未知")

    print("\n[依赖检查]")
    has_torch = importlib.util.find_spec("torch") is not None
    info("torch", "已安装" if has_torch else "未安装")

    if not has_torch:
        print("\n  ⚠ 未安装 PyTorch。按你的机器选择：")
        print("  · Windows（CUDA 12.1）：")
        print("      pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121")
        print("  · Mac（Apple Silicon）：")
        print("      pip install torch torchvision torchaudio")
        print("\n  安装后重新运行本脚本。")
        return 0

    import torch

    info("torch 版本", torch.__version__)

    print("\n[计算后端]")
    cuda_ok = torch.cuda.is_available()
    mps_ok = bool(
        getattr(torch.backends, "mps", None)
        and torch.backends.mps.is_available()
    )
    info("CUDA 可用", "✅ 是" if cuda_ok else "❌ 否")
    info("MPS 可用", "✅ 是" if mps_ok else "❌ 否")

    if cuda_ok:
        info("GPU 型号", torch.cuda.get_device_name(0))
        total, _ = torch.cuda.get_device_properties(0).total_memory, None
        info("显存", f"{total / 1024**3:.1f} GB")
        info("CUDA 版本", torch.version.cuda or "未知")

    # 得出推荐配置
    print("\n[推荐配置]")
    if cuda_ok:
        device, dtype = "cuda", "float16"
        note = "家里主机：使用标准 CUDA 流程，W20 LoRA / W23 vLLM 都在这台跑"
    elif mps_ok:
        device, dtype = "mps", "float32"
        note = "Mac：MPS 对 fp16 支持不完整，用 fp32；7B LoRA 慢，重训练挪到 Windows"
    else:
        device, dtype = "cpu", "float32"
        note = "只有 CPU：小实验可行，深度学习阶段建议换机器"
    info("device", f'"{device}"')
    info("dtype", f"torch.{dtype}")
    print(f"  {'说明':<18} {note}")

    print("\n  代码模板：")
    print("    if torch.cuda.is_available():")
    print('        device, dtype = "cuda", torch.float16')
    print("    elif torch.backends.mps.is_available():")
    print('        device, dtype = "mps", torch.float32')
    print("    else:")
    print('        device, dtype = "cpu", torch.float32')

    # 仓库文件检查
    print("\n[仓库文件]")
    for rel in ["data/progress.json", "scripts/generate_stats.py", "docs/plan.html"]:
        ok = (ROOT / rel).exists()
        info(rel, "OK" if ok else "缺失")

    print("\n" + "=" * 56)
    if cuda_ok or mps_ok:
        print("  ✅ 环境就绪，可以开始实验。")
    else:
        print("  ⚠ 未检测到 GPU，深度学习阶段会较慢。")
    print("=" * 56)
    return 0


if __name__ == "__main__":
    sys.exit(main())
