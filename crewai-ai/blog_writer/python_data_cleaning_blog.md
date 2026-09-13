# Python 数据清洗入门：用 pandas 告别脏数据

在数据科学和机器学习的世界里，有一句著名的行话：“**Garbage In, Garbage Out**”（垃圾进，垃圾出）。如果你把充满错误、缺失和混乱的“脏数据”喂给模型，它只会吐出毫无价值的预测结果。真实世界的数据往往是不完美的，因此，**数据清洗**成为了每个数据分析师和算法工程师的必修课。

今天，我们将借助 Python 中最强大的数据处理库 `pandas`，带你一步步掌握自动化数据清洗的核心技巧，帮你构建自己的数据清洗流水线，彻底告别脏数据！

---

## 一、 认识四大“脏数据”及应对策略

在动手写代码之前，我们需要先了解数据中常见的四类“病症”以及如何对症下药。

### 1. 缺失值 (Missing Values)
* **症状**：数据表里空荡荡的 `NaN` 或空白。可能是传感器故障，也可能是用户注册时漏填了信息。
* **药方**：
  * **删除**：如果缺失比例极小，直接用 `df.dropna()` 删掉。
  * **填充**：更常见的做法是用统计值（均值、中位数、众数）填充，时间序列数据还可以用前向/后向填充 (`df.ffill()`, `df.bfill()`)。

### 2. 重复值 (Duplicate Values)
* **症状**：同一条记录出现了多次，会导致统计结果（如总销售额、均值）严重失真。
* **药方**：使用 `df.drop_duplicates()` 轻松去重。如果是部分字段重复（如同一个用户 ID 有多条更新记录），可以通过 `subset` 参数指定判断列，并用 `keep='last'` 保留最新的一条。

### 3. 格式不一致 (Inconsistent Formatting)
* **症状**：同一个语义的数据，长相却千奇百怪。比如日期有 `2023-01-01` 也有 `2023/1/1`；部门名称有 `IT` 也有 `it`；薪资列里混入了千分位逗号 `50,000`。
* **药方**：
  * **字符串**：用 `.str.strip()` 去首尾空格，`.str.lower()` 统一小写。
  * **日期**：用 `pd.to_datetime()` 强制标准化。
  * **数值**：用正则表达式剔除特殊字符，再用 `pd.to_numeric()` 转换。

### 4. 异常值与逻辑错误 (Outliers)
* **症状**：数据虽然填了，但违背常理。比如年龄 200 岁，或者薪资是负数。
* **药方**：设定业务阈值（如限制年龄在 18-65 岁之间），将越界的数据拦截并视为缺失值处理。

---

## 二、 实战：打造你的第一个自动化清洗流水线 (Pipeline)

为了让你在实际工作中更加优雅地处理数据，我们采用**面向对象**和**链式调用**的设计模式，封装了一个 `DataCleaner` 类。这样不仅能避免意外修改原始数据，还能让代码像工厂流水线一样清晰易读。

以下是完整可运行的代码示例：

```python
import pandas as pd
import numpy as np

class DataCleaner:
    """自动化数据清洗管道类"""
    def __init__(self, df: pd.DataFrame):
        # 复制数据以避免修改原始 DataFrame
        self.df = df.copy()
        self.cleaning_log = []

    def _log(self, step: str, rows_before: int):
        rows_after = len(self.df)
        self.cleaning_log.append(f"[{step}] 处理前行数: {rows_before} -> 处理后行数: {rows_after}")

    def remove_duplicates(self, subset=None, keep='first'):
        """1. 处理重复值"""
        rows_before = len(self.df)
        self.df = self.df.drop_duplicates(subset=subset, keep=keep).reset_index(drop=True)
        self._log("去除重复值", rows_before)
        return self

    def standardize_strings(self, columns):
        """2. 处理字符串格式不一致（去空格、统一小写）"""
        rows_before = len(self.df)
        for col in columns:
            if self.df[col].dtype == 'object' or pd.api.types.is_string_dtype(self.df[col]):
                self.df[col] = self.df[col].astype(str).str.strip().str.lower()
        self._log("字符串标准化", rows_before)
        return self

    def clean_and_convert_numeric(self, column, regex_pattern=r'[^0-9.\-]'):
        """3. 清理数值列中的特殊字符并转换类型"""
        rows_before = len(self.df)
        # 使用正则表达式替换掉非数字、非小数点、非负号的字符
        self.df[column] = self.df[column].astype(str).str.replace(regex_pattern, '', regex=True)
        # 转换为数值类型，无法转换的变为 NaN
        self.df[column] = pd.to_numeric(self.df[column], errors='coerce')
        self._log(f"数值清洗与转换 ({column})", rows_before)
        return self

    def standardize_dates(self, column):
        """4. 统一日期格式"""
        rows_before = len(self.df)
        self.df[column] = pd.to_datetime(self.df[column], errors='coerce')
        self._log(f"日期标准化 ({column})", rows_before)
        return self

    def handle_outliers(self, column, lower_bound, upper_bound):
        """5. 处理异常值（将超出业务逻辑范围的值视为缺失值）"""
        rows_before = len(self.df)
        mask = (self.df[column] < lower_bound) | (self.df[column] > upper_bound)
        self.df.loc[mask, column] = np.nan
        self._log(f"异常值处理 ({column})", rows_before)
        return self

    def impute_missing_values(self, num_strategy='median', cat_fill_value='unknown'):
        """6. 处理缺失值"""
        rows_before = len(self.df)
        for col in self.df.columns:
            if self.df[col].isna().sum() > 0:
                if pd.api.types.is_numeric_dtype(self.df[col]):
                    fill_val = self.df[col].median() if num_strategy == 'median' else self.df[col].mean()
                    self.df[col].fillna(fill_val, inplace=True)
                elif pd.api.types.is_datetime64_any_dtype(self.df[col]):
                    self.df[col].fillna(self.df[col].dropna().median(), inplace=True)
                else:
                    self.df[col].fillna(cat_fill_value, inplace=True)
        self._log("缺失值填充", rows_before)
        return self

    def get_result(self):
        return self.df

    def print_log(self):
        print("--- 数据清洗日志 ---")
        for log in self.cleaning_log: print(log)
        print("--------------------")

# ==========================================
# 测试与执行
# ==========================================
if __name__ == "__main__":
    # 模拟真实世界的脏数据
    dirty_data = {
        'emp_id': [1, 2, 2, 3, 4, 5],
        'name': [' Alice ', 'bob', 'BOB', 'Charlie', 'David', 'Eve'],
        'age': [25, 30, 30, np.nan, 150, 35],  # 包含缺失值和异常值(150)
        'salary': ['50,000', '60000', '60000', '75,000', 'invalid', '90,000'], # 格式不一
        'join_date': ['2021-01-01', '2021/02/15', '2021/02/15', '2021-03-10', 'Not-a-date', '2021-05-20'],
        'department': ['IT', 'it', 'IT', 'HR', 'Sales', np.nan]
    }
    raw_df = pd.DataFrame(dirty_data)
    
    # 实例化清洗管道并执行链式调用
    cleaner = DataCleaner(raw_df)
    clean_df = (cleaner
        .remove_duplicates(subset=['emp_id'], keep='first')       
        .standardize_strings(columns=['name', 'department'])      
        .clean_and_convert_numeric(column='salary')               
        .standardize_dates(column='join_date')                    
        .handle_outliers(column='age', lower_bound=18, upper_bound=65) 
        .impute_missing_values(num_strategy='median', cat_fill_value='unassigned') 
        .get_result()
    )
    
    cleaner.print_log()
    print("\n========== 清洗后的干净数据 ==========")
    print(clean_df)
```

---

## 三、 代码解析：流水线做了什么？

1. **去重与字符串标准化**：`emp_id=2` 的重复行被剔除；`' Alice '` 变成了干净的 `'alice'`，`'IT'` 和 `'it'` 被统一，消除了分类特征中的伪基数问题。
2. **数值与日期清洗**：薪资列的 `'50,000'` 被正确解析为 `50000.0`，而 `'invalid'` 被安全地转换为 `NaN`；各种奇奇怪怪的日期格式被统一转换为标准的 `datetime64` 类型。
3. **异常值拦截与兜底**：`age=150` 违背生理常识，被拦截并置为 `NaN`。最后一步，所有残留的 `NaN` 均根据数据类型（数值型用中位数，类别型用 `'unassigned'`）完成了填充，确保输出的数据可以直接输入到机器学习模型中。

---

## 四、 新手避坑指南（最佳实践）

在结束之前，送给大家 4 条数据清洗的“黄金法则”：

1. **防御性编程**：在进行类型转换（如 `pd.to_numeric`, `pd.to_datetime`）时，务必加上 `errors='coerce'` 参数。这能防止个别极端脏数据导致整个程序崩溃，将其转化为 `NaN` 留待后续统一处理。
2. **警惕数据泄露**：在机器学习场景中，缺失值的填充（如均值）**必须**基于训练集计算，然后再应用到测试集。千万不要用全局数据的均值去填充，否则会导致模型“偷看”未来的答案。
3. **保持数据不可变性**：在封装清洗逻辑时，第一步一定要用 `df.copy()` 复制数据。这保证了原始数据不被意外篡改，方便你随时回溯。
4. **善用正则表达式**：对于包含货币符号、千分位逗号的字符串数值列，`str.replace(r'[^0-9.\-]', '', regex=True)` 是最健壮、最省心的清洗方案。

## 结语

数据清洗虽然往往占据了数据科学家 80% 的时间，但它绝不是枯燥的体力活。通过合理的抽象和工具（如 `pandas`），我们完全可以将它变成一门优雅的艺术。希望这篇入门指南能帮你建立起数据清洗的系统思维，赶快打开 Jupyter Notebook，用你的代码去征服那些“脏数据”吧！