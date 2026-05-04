# 用户私有数据集目录

此目录用于存储用户上传的私有数据集。

## 目录结构

```
user_datasets/
├── {user_id}/              # 用户ID目录
│   ├── {category}/         # 分类目录（可选，用户自定义）
│   │   └── dataset.jsonl   # 数据集文件
│   └── dataset.jsonl       # 数据集文件
└── README.md
```

## 数据集格式

每个 `.jsonl` 文件包含多行 JSON 对象，每行一个样本：

```json
{"subtype": "风险子类型", "poc": "测试样本内容"}
```

## 示例

```
user_datasets/
├── 1/                      # 用户ID=1
│   ├── custom_attack/
│   │   └── my_dataset.jsonl
│   └── test.jsonl
└── 2/                      # 用户ID=2
    └── private_test.jsonl
```

加载后的数据集名称格式：`user_{user_id}/{相对路径}`

例如：
- `user_1/custom_attack/my_dataset`
- `user_1/test`
- `user_2/private_test`
