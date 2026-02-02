======================================================================
P1剩余函数重构模板
======================================================================

## extract_from_text() - 复杂度21, 135行
**文件**: `apps/patent-platform/workspace/process_all_patents.py:206`

### 重构建议
- 分离文本解析和字段提取
- 提取实体验证逻辑
- 提取关系推断逻辑

### 重构模板
```python
class ExtractFromTextHandler:
    """extract_from_text处理器"""

    def handle(self, *args, **kwargs):
        """处理extract_from_text"""
        # 1. 准备
        prepared = self._prepare(*args, **kwargs)

        # 2. 执行
        result = self._execute(prepared)

        # 3. 返回
        return self._format_result(result)

    def _prepare(self, *args, **kwargs):
        """准备数据"""
        pass

    def _execute(self, prepared):
        """执行逻辑"""
        pass

    def _format_result(self, result):
        """格式化结果"""
        pass
```

----------------------------------------------------------------------

## assign_patent_task() - 复杂度21, 109行
**文件**: `apps/patent-platform/workspace/src/communication/patent_communication_enhancer.py:467`

### 重构建议
- 提取优先级计算逻辑
- 提取代理选择逻辑
- 提取任务创建逻辑

### 重构模板
```python
class AssignPatentTaskHandler:
    """assign_patent_task处理器"""

    def handle(self, *args, **kwargs):
        """处理assign_patent_task"""
        # 1. 准备
        prepared = self._prepare(*args, **kwargs)

        # 2. 执行
        result = self._execute(prepared)

        # 3. 返回
        return self._format_result(result)

    def _prepare(self, *args, **kwargs):
        """准备数据"""
        pass

    def _execute(self, prepared):
        """执行逻辑"""
        pass

    def _format_result(self, result):
        """格式化结果"""
        pass
```

----------------------------------------------------------------------

## show_found_patents() - 复杂度19, 198行
**文件**: `apps/xiaonuo/found_su_patents.py:20`

### 重构建议
- 分离数据获取逻辑
- 分离格式化逻辑
- 分离渲染逻辑

### 重构模板
```python
class ShowFoundPatentsHandler:
    """show_found_patents处理器"""

    def handle(self, *args, **kwargs):
        """处理show_found_patents"""
        # 1. 准备
        prepared = self._prepare(*args, **kwargs)

        # 2. 执行
        result = self._execute(prepared)

        # 3. 返回
        return self._format_result(result)

    def _prepare(self, *args, **kwargs):
        """准备数据"""
        pass

    def _execute(self, prepared):
        """执行逻辑"""
        pass

    def _format_result(self, result):
        """格式化结果"""
        pass
```

----------------------------------------------------------------------
