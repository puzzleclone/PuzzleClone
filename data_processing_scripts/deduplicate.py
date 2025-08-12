import json
import os
import re
import argparse
from typing import Dict, Any, Tuple, List, Union

def to_hashable(obj: Any, key_name: str = None) -> Any:
    """
    将可能的数据结构转换为可哈希类型，支持特殊数值模式和嵌套字典。
    仅当键名为"pool"且值为嵌套数组时，对最外层数组排序；其他情况保持原有顺序。
    """
    if isinstance(obj, dict):
        # 嵌套字典递归处理，传递当前键名
        return tuple(sorted((k, to_hashable(v, key_name=k)) for k, v in obj.items()))
    elif isinstance(obj, list) or isinstance(obj, tuple):
        # 处理嵌套数组：仅当键名为"pool"且元素为嵌套数组时才排序外层
        processed_items = []
        for item in obj:
            if isinstance(item, (list, tuple)):
                processed_items.append(tuple(to_hashable(subitem, key_name=None) for subitem in item))
            else:
                processed_items.append(to_hashable(item, key_name=None))
        
        # 仅对键名为"pool"的嵌套数组进行外层排序
        if key_name == "pool" and any(isinstance(item, tuple) for item in processed_items):
            return tuple(sorted(processed_items))
        else:
            return tuple(processed_items)
    elif isinstance(obj, str) and re.match(r"^__(\d+)__$", obj):
        # 处理特殊数值模式 "__x__"
        return int(re.match(r"^__(\d+)__$", obj).group(1))
    elif isinstance(obj, str) and re.match(r"^__(\d+\.\d+)__$", obj):
        # 处理特殊数值模式 "__x.y__"
        return float(re.match(r"^__(\d+\.\d+)__$", obj).group(1))
    else:
        # 基础类型直接返回
        return obj

def is_numeric_value(value: Any) -> bool:
    """
    检查值是否为数值型，包括特殊数值模式
    """
    if isinstance(value, (int, float)):
        return True
    elif isinstance(value, list):
        # 递归检查列表中的元素
        return all(is_numeric_value(item) for item in value)
    elif isinstance(value, str) and re.match(r"^__(\d+(\.\d+)?)__$", value):
        # 特殊数值模式字符串
        return True
    elif isinstance(value, tuple):
        # 递归检查元组中的元素
        return all(is_numeric_value(item) for item in value)
    elif isinstance(value, dict):
        # 嵌套字典需要递归处理
        return True
    return False

def extract_numeric_values(config: Dict[str, Any], prefix: str = "") -> List[Tuple[str, Any]]:
    """
    递归提取嵌套字典中的所有数值型键值对
    """
    numeric_items = []
    
    for key, value in config.items():
        if key == '_query':
            continue
        # 创建带前缀的完整键名
        full_key = f"{prefix}.{key}" if prefix else key
        
        # 检查是否为数值型
        if is_numeric_value(value):
            if isinstance(value, dict):
                # 递归处理嵌套字典
                numeric_items.extend(extract_numeric_values(value, full_key))
            else:
                # 对数值型值进行规范化处理（传递键名信息）
                hashable_value = to_hashable(value, key_name=key)
                numeric_items.append((full_key, hashable_value))
    
    return numeric_items

def get_numeric_signature(config: Dict[str, Any]) -> Tuple[Tuple[str, Any]]:
    """
    提取config中的数值特征签名，支持嵌套字典和特殊数值模式
    """
    # 递归提取所有数值型键值对
    numeric_items = extract_numeric_values(config)
    
    # 按key排序以确保顺序一致性
    numeric_items.sort(key=lambda x: x[0])
    
    return tuple(numeric_items)

def deduplicate_jsonl_file(input_path: str, output_path: str) -> None:
    """
    对单个JSONL文件进行去重处理，将结果写入输出文件
    """
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(input_path, 'r', encoding='utf-8') as infile:
        signatures_seen = set()
        unique_records = []
        
        # 遍历文件的每一行
        for line in infile:
            try:
                record = json.loads(line)
                config = record.get("config", {})
                
                # 获取数值特征签名
                signature = get_numeric_signature(config)
                
                # 如果没有数值型配置项或者签名未出现过，则保留该记录
                if not signature or signature not in signatures_seen:
                    unique_records.append(line)
                    if signature:
                        signatures_seen.add(signature)
                    
            except json.JSONDecodeError:
                print(f"警告: 跳过无效的JSON行: {line.strip()}")
                continue
        
        # 写入去重后的记录到输出文件
        with open(output_path, 'w', encoding='utf-8') as outfile:
            outfile.writelines(unique_records)

def process_jsonl_files(input_dir: str, output_dir: str) -> None:
    """
    处理输入目录中的所有jsonl文件，去重后输出到输出目录
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 遍历输入目录中的所有jsonl文件
    for filename in os.listdir(input_dir):
        if filename.endswith('.jsonl'):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename)
            
            print(f"正在处理文件: {filename}")
            deduplicate_jsonl_file(input_path, output_path)
            print(f"已保存去重结果到: {output_path}")

# 使用示例
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='处理JSONL文件')
    parser.add_argument('-i', '--input', default='puzzle_clone_public/data', help='输入文件夹路径，默认为"puzzle_clone_public/data"')
    parser.add_argument('-o', '--output', default='puzzle_clone_public/deduplicated_data', help='输出文件夹路径，默认为puzzle_clone_public/deduplicated_data')
    
    args = parser.parse_args()
    
    print("开始处理文件去重...")
    process_jsonl_files(args.input, args.output)
    print("去重处理完成！")