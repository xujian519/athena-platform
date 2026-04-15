#!/usr/bin/env python3
"""
法条智能画像API服务
作者: 小诺·双鱼公主 v4.0.0
"""

from __future__ import annotations
import logging
from typing import Any

from flask import Flask, jsonify, request
from law_profiler_service import LawArticleProfiler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
profiler = LawArticleProfiler()

@app.route('/health', methods=['GET'])
def health() -> Any:
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "service": "law_profiler",
        "version": "1.0.0",
        "generator": "小诺·双鱼公主 v4.0.0"
    })

@app.route('/profile/<law_id>', methods=['GET'])
def get_profile(law_id) -> None:
    """
    获取法条画像

    参数:
    - law_id: 法条ID或名称

    返回: 完整画像JSON
    """
    try:
        profile_type = request.args.get('type', 'full')  # full, basic, application, relation, practice

        if profile_type == 'full':
            profile = profiler.get_full_profile(law_id)
        elif profile_type == 'basic':
            profile = profiler.get_basic_profile(law_id)
        elif profile_type == 'application':
            profile = profiler.get_application_profile(law_id)
        elif profile_type == 'relation':
            profile = profiler.get_relation_profile(law_id)
        elif profile_type == 'practice':
            profile = profiler.get_practice_profile(law_id)
        else:
            return jsonify({"error": "无效的profile_type"}), 400

        return jsonify({
            "success": True,
            "law_id": law_id,
            "profile_type": profile_type,
            "data": profile
        })

    except Exception as e:
        logger.error(f"❌ 获取画像失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/profile/batch', methods=['POST'])
def get_batch_profiles() -> Any | None:
    """
    批量获取法条画像

    Body: {"law_ids": ["法条1", "法条2", ...]}
    """
    try:
        data = request.get_json()
        law_ids = data.get('law_ids', [])

        if not law_ids:
            return jsonify({"error": "未提供law_ids"}), 400

        profiles = {}
        for law_id in law_ids:
            try:
                profile = profiler.get_full_profile(law_id)
                profiles[law_id] = {
                    "success": True,
                    "data": profile
                }
            except Exception as e:
                profiles[law_id] = {
                    "success": False,
                    "error": str(e)
                }

        return jsonify({
            "success": True,
            "total": len(law_ids),
            "profiles": profiles
        })

    except Exception as e:
        logger.error(f"❌ 批量获取失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/profile/format/<law_id>', methods=['GET'])
def get_formatted_profile(law_id) -> None:
    """
    获取格式化的法条画像(用于显示)
    """
    try:
        profile = profiler.get_full_profile(law_id)
        formatted = profiler.format_profile_for_display(profile)

        return jsonify({
            "success": True,
            "law_id": law_id,
            "formatted_profile": formatted
        })

    except Exception as e:
        logger.error(f"❌ 获取格式化画像失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    logger.info("🚀 法条智能画像API服务启动")
    logger.info("📡 端口: 5001")
    logger.info("🎯 作者: 小诺·双鱼公主 v4.0.0")
    app.run(host='0.0.0.0', port=5001, debug=True)
