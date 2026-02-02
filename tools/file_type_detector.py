#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件类型检测器 - Athena工作平台多模态文件处理系统
File Type Detector - Multimodal File Processing System for Athena Platform

智能识别和处理多种文件格式，提供统一的文件管理接口

作者: Athena AI系统
创建时间: 2025年12月6日
版本: 1.0.0
"""

import hashlib
import json
import logging
import mimetypes
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import magic

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [FileTypeDetector] %(message)s',
    handlers=[
        logging.FileHandler(f'file_detector_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FileTypeDetector:
    """智能文件类型检测器"""

    def __init__(self):
        self.supported_formats = {
            # 图像文件
            'image': {
                'extensions': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.ico', '.tiff'],
                'mime_types': ['image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/webp', 'image/svg+xml'],
                'processor': 'image_processor',
                'description': '图像文件'
            },

            # 文档文件
            'document': {
                'extensions': ['.pdf', '.doc', '.docx', '.txt', '.md', '.rtf', '.odt', '.pages', '.epub'],
                'mime_types': ['application/pdf', 'application/msword', 'text/plain', 'text/markdown'],
                'processor': 'document_processor',
                'description': '文档文件'
            },

            # 音频文件
            'audio': {
                'extensions': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma'],
                'mime_types': ['audio/mpeg', 'audio/wav', 'audio/flac', 'audio/ogg'],
                'processor': 'audio_processor',
                'description': '音频文件'
            },

            # 视频文件
            'video': {
                'extensions': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'],
                'mime_types': ['video/mp4', 'video/avi', 'video/quicktime', 'video/x-matroska'],
                'processor': 'video_processor',
                'description': '视频文件'
            },

            # 数据文件
            'data': {
                'extensions': ['.json', '.xml', '.csv', '.xlsx', '.xls', '.yaml', '.yml', '.sql', '.db', '.sqlite'],
                'mime_types': ['application/json', 'text/xml', 'text/csv', 'application/vnd.ms-excel'],
                'processor': 'data_processor',
                'description': '数据文件'
            },

            # 代码文件
            'code': {
                'extensions': ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.h', '.go', '.rs', '.php'],
                'mime_types': ['text/x-python', 'text/javascript', 'text/html', 'text/css'],
                'processor': 'code_processor',
                'description': '代码文件'
            },

            # 压缩文件
            'archive': {
                'extensions': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz'],
                'mime_types': ['application/zip', 'application/x-rar-compressed', 'application/x-7z-compressed'],
                'processor': 'archive_processor',
                'description': '压缩文件'
            },

            # 演示文件
            'presentation': {
                'extensions': ['.ppt', '.pptx', '.key', '.odp'],
                'mime_types': ['application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation'],
                'processor': 'presentation_processor',
                'description': '演示文件'
            }
        }

        # 统计信息
        self.stats = {
            'total_files': 0,
            'detected_files': 0,
            'supported_files': 0,
            'unsupported_files': 0,
            'type_distribution': {}
        }

    def detect_file_type(self, file_path: str) -> Dict[str, Any]:
        """
        检测文件类型

        Args:
            file_path: 文件路径

        Returns:
            Dict: 包含文件类型信息的字典
        """
        try:
            file_path = Path(file_path)

            if not file_path.exists():
                return {
                    'error': '文件不存在',
                    'file_path': str(file_path),
                    'file_type': 'unknown'
                }

            # 获取基础文件信息
            basic_info = self._get_basic_info(file_path)

            # 尝试多种检测方法
            detection_methods = [
                self._detect_by_extension,
                self._detect_by_mime_type,
                self._detect_by_magic_number,
                self._detect_by_content_analysis
            ]

            file_type_info = None
            for method in detection_methods:
                try:
                    result = method(file_path, basic_info)
                    if result and result.get('type') != 'unknown':
                        file_type_info = result
                        break
                except Exception as e:
                    logger.warning(f"检测方法失败 {method.__name__}: {e}")
                    continue

            # 如果所有方法都失败，返回默认结果
            if not file_type_info:
                file_type_info = {
                    'type': 'unknown',
                    'confidence': 0.0,
                    'method': 'fallback'
                }

            # 合并所有信息
            result = {
                'file_path': str(file_path),
                'file_name': file_path.name,
                'file_size': file_path.stat().st_size,
                'file_modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                'detected_type': file_type_info['type'],
                'type_confidence': file_type_info.get('confidence', 0.0),
                'detection_method': file_type_info.get('method', 'unknown'),
                'mime_type': file_type_info.get('mime_type', 'application/octet-stream'),
                'category': file_type_info.get('category', 'unknown'),
                'processor': file_type_info.get('processor', None),
                'description': file_type_info.get('description', '未知文件类型'),
                'is_supported': file_type_info['type'] in self.supported_formats,
                'file_hash': self._calculate_file_hash(file_path),
                'basic_info': basic_info
            }

            # 更新统计信息
            self._update_stats(result)

            return result

        except Exception as e:
            logger.error(f"检测文件类型时出错 {file_path}: {e}")
            return {
                'error': str(e),
                'file_path': str(file_path),
                'file_type': 'error'
            }

    def _get_basic_info(self, file_path: Path) -> Dict[str, Any]:
        """获取基础文件信息"""
        try:
            stat = file_path.stat()
            return {
                'size_bytes': stat.st_size,
                'size_human': self._format_size(stat.st_size),
                'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'created_time': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'extension': file_path.suffix.lower(),
                'name_without_ext': file_path.stem
            }
        except Exception as e:
            logger.error(f"获取基础文件信息失败 {file_path}: {e}")
            return {}

    def _detect_by_extension(self, file_path: Path, basic_info: Dict) -> Dict[str, Any | None]:
        """通过文件扩展名检测"""
        extension = basic_info.get('extension', '').lower()

        for file_type, config in self.supported_formats.items():
            if extension in config['extensions']:
                return {
                    'type': file_type,
                    'confidence': 0.9,
                    'method': 'extension',
                    'mime_type': self._get_mime_type(file_path),
                    'category': file_type,
                    'processor': config['processor'],
                    'description': config['description']
                }

        return None

    def _detect_by_mime_type(self, file_path: Path, basic_info: Dict) -> Dict[str, Any | None]:
        """通过MIME类型检测"""
        mime_type = self._get_mime_type(file_path)

        for file_type, config in self.supported_formats.items():
            if mime_type in config.get('mime_types', []):
                return {
                    'type': file_type,
                    'confidence': 0.95,
                    'method': 'mime_type',
                    'mime_type': mime_type,
                    'category': file_type,
                    'processor': config['processor'],
                    'description': config['description']
                }

        return None

    def _detect_by_magic_number(self, file_path: Path, basic_info: Dict) -> Dict[str, Any | None]:
        """通过魔术数字检测"""
        try:
            if not hasattr(self, 'mime'):
                self.mime = magic.Magic(mime=True)

            mime_type = self.mime.from_file(str(file_path))

            # 特殊处理某些文件类型
            if mime_type == 'application/zip':
                # 可能是docx, xlsx等
                if basic_info.get('extension') in ['.docx', '.xlsx', '.pptx']:
                    file_type_map = {
                        '.docx': 'document',
                        '.xlsx': 'data',
                        '.pptx': 'presentation'
                    }
                    file_type = file_type_map.get(basic_info.get('extension'), 'archive')

                    return {
                        'type': file_type,
                        'confidence': 0.85,
                        'method': 'magic_number',
                        'mime_type': mime_type,
                        'category': file_type,
                        'processor': self.supported_formats[file_type]['processor'],
                        'description': self.supported_formats[file_type]['description']
                    }

            # 通用MIME类型检测
            for file_type, config in self.supported_formats.items():
                if any(mt in mime_type for mt in config.get('mime_types', [])):
                    return {
                        'type': file_type,
                        'confidence': 0.9,
                        'method': 'magic_number',
                        'mime_type': mime_type,
                        'category': file_type,
                        'processor': config['processor'],
                        'description': config['description']
                    }

            return None

        except Exception as e:
            logger.warning(f"魔术数字检测失败 {file_path}: {e}")
            return None

    def _detect_by_content_analysis(self, file_path: Path, basic_info: Dict) -> Dict[str, Any | None]:
        """通过内容分析检测"""
        try:
            # 只对文本文件进行内容分析
            if basic_info.get('size_bytes', 0) > 10 * 1024 * 1024:  # 10MB
                return None

            # 读取文件头部
            with open(file_path, 'rb') as f:
                header = f.read(1024)

            # 分析文件头标识
            header_signatures = {
                b'PK\x03\x04': ('archive', 0.9),  # ZIP/DOCX/XLSX
                b'%PDF': ('document', 0.95),     # PDF
                b'\x89PNG': ('image', 0.95),     # PNG
                b'\xff\xd8\xff': ('image', 0.95), # JPEG
                b'GIF8': ('image', 0.9),         # GIF
                b'RIFF': ('video', 0.8),         # AVI/WAV
                b'\x1a\x45\xdf\xa3': ('video', 0.9), # MKV
            }

            for signature, (file_type, confidence) in header_signatures.items():
                if header.startswith(signature):
                    if file_type in self.supported_formats:
                        config = self.supported_formats[file_type]
                        return {
                            'type': file_type,
                            'confidence': confidence,
                            'method': 'content_analysis',
                            'category': file_type,
                            'processor': config['processor'],
                            'description': config['description']
                        }

            # 代码文件检测
            if b'import ' in header or b'from ' in header or b'def ' in header:
                return {
                    'type': 'code',
                    'confidence': 0.7,
                    'method': 'content_analysis',
                    'category': 'code',
                    'processor': 'code_processor',
                    'description': '代码文件'
                }

            return None

        except Exception as e:
            logger.warning(f"内容分析检测失败 {file_path}: {e}")
            return None

    def _get_mime_type(self, file_path: Path) -> str:
        """获取MIME类型"""
        try:
            mime_type, _ = mimetypes.guess_type(str(file_path))
            return mime_type or 'application/octet-stream'
        except:
            return 'application/octet-stream'

    def _calculate_file_hash(self, file_path: Path) -> str:
        """计算文件哈希值"""
        try:
            hash_md5 = hashlib.md5(usedforsecurity=False)
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except:
            return ''

    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f}PB"

    def _update_stats(self, result: Dict[str, Any]):
        """更新统计信息"""
        self.stats['total_files'] += 1

        if 'error' not in result:
            self.stats['detected_files'] += 1

            if result['is_supported']:
                self.stats['supported_files'] += 1
            else:
                self.stats['unsupported_files'] += 1

            file_type = result['detected_type']
            if file_type not in self.stats['type_distribution']:
                self.stats['type_distribution'][file_type] = 0
            self.stats['type_distribution'][file_type] += 1

    def scan_directory(self, directory: str, recursive: bool = True) -> List[Dict[str, Any]]:
        """
        扫描目录中的所有文件

        Args:
            directory: 目录路径
            recursive: 是否递归扫描子目录

        Returns:
            List[Dict]: 文件检测结果列表
        """
        logger.info(f"开始扫描目录: {directory}")

        directory_path = Path(directory)
        if not directory_path.exists():
            logger.error(f"目录不存在: {directory}")
            return []

        files_found = []
        pattern = '**/*' if recursive else '*'

        try:
            for file_path in directory_path.glob(pattern):
                if file_path.is_file():
                    logger.debug(f"检测文件: {file_path}")
                    result = self.detect_file_type(file_path)
                    files_found.append(result)

        except Exception as e:
            logger.error(f"扫描目录时出错 {directory}: {e}")

        logger.info(f"扫描完成，共检测 {len(files_found)} 个文件")
        return files_found

    def get_supported_formats(self) -> Dict[str, Any]:
        """获取支持的文件格式"""
        return {
            'total_types': len(self.supported_formats),
            'formats': self.supported_formats,
            'total_extensions': sum(len(config['extensions']) for config in self.supported_formats.values())
        }

    def get_statistics(self) -> Dict[str, Any]:
        """获取检测统计信息"""
        return {
            'detection_stats': self.stats.copy(),
            'supported_formats': self.get_supported_formats(),
            'detection_methods': ['extension', 'mime_type', 'magic_number', 'content_analysis'],
            'confidence_levels': ['high (>0.8)', 'medium (0.5-0.8)', 'low (<0.5)']
        }

    def export_results(self, results: List[Dict[str, Any]], output_file: str = None):
        """导出检测结果到文件"""
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"file_detection_results_{timestamp}.json"

        export_data = {
            'export_time': datetime.now().isoformat(),
            'total_files': len(results),
            'statistics': self.get_statistics(),
            'results': results
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        logger.info(f"检测结果已导出到: {output_file}")
        return output_file

def main():
    """主函数 - 演示文件类型检测器"""
    logger.info('🔍 文件类型检测器演示')
    logger.info(str('=' * 50))

    detector = FileTypeDetector()

    # 显示支持的格式
    formats = detector.get_supported_formats()
    logger.info(f"📋 支持的文件格式:")
    logger.info(f"   文件类型: {formats['total_types']} 种")
    logger.info(f"   扩展名: {formats['total_extensions']} 个")
    logger.info(f"   检测方法: 4 种 (扩展名/MIME/魔术数字/内容分析)")

    # 扫描当前目录
    logger.info(f"\n🔍 开始扫描当前目录...")
    results = detector.scan_directory('.', recursive=False)

    # 统计结果
    stats = detector.get_statistics()
    logger.info(f"\n📊 扫描结果统计:")
    logger.info(f"   总文件数: {stats['detection_stats']['total_files']}")
    logger.info(f"   成功检测: {stats['detection_stats']['detected_files']}")
    logger.info(f"   支持格式: {stats['detection_stats']['supported_files']}")
    logger.info(f"   不支持: {stats['detection_stats']['unsupported_files']}")

    # 显示类型分布
    logger.info(f"\n📋 文件类型分布:")
    for file_type, count in stats['detection_stats']['type_distribution'].items():
        logger.info(f"   {file_type}: {count} 个")

    # 导出结果
    if results:
        output_file = detector.export_results(results)
        logger.info(f"\n💾 结果已导出到: {output_file}")

if __name__ == '__main__':
    main()