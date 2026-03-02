#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复知识库中重复ID的脚本
该脚本会：
1. 读取 knowledge.json 文件
2. 检测重复的ID
3. 重新分配唯一的ID（从1开始递增）
4. 创建备份文件
5. 保存更新后的数据
"""

import os
import json
import shutil
from datetime import datetime

def fix_knowledge_ids():
    # 获取文件路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    uploads_dir = os.path.join(script_dir, 'uploads')
    kb_path = os.path.join(uploads_dir, 'knowledge.json')
    
    # 检查文件是否存在
    if not os.path.exists(kb_path):
        print(f"错误：文件不存在 {kb_path}")
        return False
    
    # 读取原始数据
    print(f"正在读取 {kb_path}...")
    try:
        with open(kb_path, 'r', encoding='utf-8') as f:
            kb_list = json.load(f)
    except Exception as e:
        print(f"读取文件失败: {e}")
        return False
    
    if not isinstance(kb_list, list):
        print("错误：数据格式不正确，应为列表")
        return False
    
    print(f"找到 {len(kb_list)} 个文档")
    
    # 检测重复ID
    id_count = {}
    duplicates = []
    for idx, item in enumerate(kb_list):
        item_id = item.get('id')
        if item_id is None:
            print(f"警告：第 {idx + 1} 个文档没有ID字段")
            continue
        
        if item_id in id_count:
            id_count[item_id].append(idx)
            duplicates.append(item_id)
        else:
            id_count[item_id] = [idx]
    
    if duplicates:
        print(f"\n发现重复的ID: {set(duplicates)}")
        for dup_id in set(duplicates):
            indices = id_count[dup_id]
            print(f"  ID {dup_id} 出现在 {len(indices)} 个文档中（索引: {indices}）")
    else:
        print("\n未发现重复ID，但将重新分配ID以确保连续")
    
    # 创建备份
    backup_path = kb_path + f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"\n创建备份文件: {backup_path}")
    try:
        shutil.copy2(kb_path, backup_path)
        print("备份创建成功")
    except Exception as e:
        print(f"警告：备份创建失败: {e}")
        # 非交互模式：如果备份失败，仍然继续
        print("继续执行修复...")
    
    # 重新分配ID（从1开始，每个文档都分配唯一ID）
    print("\n重新分配ID...")
    current_id = 1
    
    # 直接为每个文档分配新的唯一ID，不管原来的ID是什么
    for item in kb_list:
        old_id = item.get('id')
        # 直接分配新ID，确保每个文档都有唯一ID
        item['id'] = current_id
        # 同时更新或添加docId字段，确保docId和id保持一致
        item['docId'] = current_id
        current_id += 1
    
    print(f"已重新分配ID，新ID范围: 1 - {current_id - 1}")
    
    # 验证新ID的唯一性
    new_ids = [item.get('id') for item in kb_list if item.get('id') is not None]
    if len(new_ids) != len(set(new_ids)):
        print("错误：重新分配后仍有重复ID！")
        return False
    
    # 保存更新后的数据
    print(f"\n保存更新后的数据到 {kb_path}...")
    try:
        with open(kb_path, 'w', encoding='utf-8') as f:
            json.dump(kb_list, f, ensure_ascii=False, indent=2)
        print("保存成功！")
    except Exception as e:
        print(f"保存失败: {e}")
        return False
    
    # 显示统计信息
    print("\n修复完成！")
    print(f"总文档数: {len(kb_list)}")
    print(f"唯一ID数: {len(set(new_ids))}")
    if duplicates:
        print(f"修复的重复ID数: {len(set(duplicates))}")
    print(f"备份文件: {backup_path}")
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("知识库ID修复脚本")
    print("=" * 60)
    
    success = fix_knowledge_ids()
    
    if success:
        print("\n✓ 修复成功！")
    else:
        print("\n✗ 修复失败！")
        exit(1)

