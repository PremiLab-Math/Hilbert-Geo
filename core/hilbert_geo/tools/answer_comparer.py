"""
答案比较工具 - 支持包含变量的复杂表达式比较
使用SymPy进行符号数学运算，可以准确判断表达式的等价性
"""
import sympy
from sympy import symbols, simplify, expand, factor, cancel, pi, E
from sympy.parsing.sympy_parser import parse_expr
import warnings


def normalize_expression(expr_str):
    """
    规范化表达式字符串，转换为SymPy可以解析的格式
    
    Args:
        expr_str: 表达式字符串，如 "5*(5*x+7)/(2*x+3)" 或 "x**3+12*x**2+48*x+64"
    
    Returns:
        SymPy表达式对象，如果解析失败返回None
    """
    if not expr_str or not isinstance(expr_str, str):
        return None
    
    # 预处理：替换常见的数学符号
    expr_str = expr_str.strip()
    
    # 移除空格
    expr_str = expr_str.replace(' ', '')
    
    # 处理特殊情况：pi已经是符号，不需要替换
    # 处理特殊情况：sqrt(x) 已经是函数，不需要替换
    
    try:
        # 使用SymPy解析表达式
        # 自动创建未定义的符号（如x, y等）
        expr = parse_expr(expr_str, transformations='all')
        return expr
    except Exception as e:
        warnings.warn(f"Failed to parse expression '{expr_str}': {e}")
        return None


def expressions_equal(expr1_str, expr2_str, tolerance=1e-10):
    """
    比较两个表达式是否等价（数学上相等）
    
    支持：
    - 数值表达式：如 "200", "125.3"
    - 包含变量的表达式：如 "5*(5*x+7)/(2*x+3)", "x**3+12*x**2+48*x+64"
    - 包含常量的表达式：如 "63*pi*x*x*x+66*pi*x*x+15*pi*x"
    - 分数表达式：如 "847/3"
    
    Args:
        expr1_str: 第一个表达式字符串
        expr2_str: 第二个表达式字符串
        tolerance: 数值比较的容差（默认1e-10）
    
    Returns:
        bool: 如果两个表达式等价返回True，否则返回False
    """
    # 处理None或空字符串
    if not expr1_str or not expr2_str:
        return str(expr1_str) == str(expr2_str)
    
    # 转换为字符串
    expr1_str = str(expr1_str).strip()
    expr2_str = str(expr2_str).strip()
    
    # 完全相同的字符串
    if expr1_str == expr2_str:
        return True
    
    # 尝试数值比较（适用于纯数字答案）
    try:
        val1 = float(expr1_str)
        val2 = float(expr2_str)
        return abs(val1 - val2) < tolerance
    except (ValueError, TypeError):
        pass
    
    # 符号表达式比较
    try:
        expr1 = normalize_expression(expr1_str)
        expr2 = normalize_expression(expr2_str)
        
        if expr1 is None or expr2 is None:
            # 如果无法解析，回退到字符串比较
            return expr1_str == expr2_str
        
        # 尝试多种方式比较
        # 1. 直接相减看是否为0
        diff = simplify(expr1 - expr2)
        if diff == 0:
            return True
        
        # 2. 尝试展开后比较
        try:
            diff_expanded = expand(diff)
            if diff_expanded == 0:
                return True
        except:
            pass
        
        # 3. 尝试因式分解后比较
        try:
            diff_factored = factor(diff)
            if diff_factored == 0:
                return True
        except:
            pass
        
        # 4. 尝试约分后比较（适用于分式）
        try:
            diff_canceled = cancel(diff)
            if diff_canceled == 0:
                return True
        except:
            pass
        
        # 5. 符号比较：检查是否所有系数都相等
        # 将表达式转换为多项式形式进行比较
        # 获取表达式中所有的符号
        symbols_in_expr = list(expr1.free_symbols | expr2.free_symbols)
        if symbols_in_expr:
            # 对于每个符号，检查系数是否相等
            # 简化后再比较
            simplified_diff = simplify(diff)
            if simplified_diff == 0:
                return True
            
            # 尝试代入随机值验证
            import random
            test_values = {}
            for sym in symbols_in_expr:
                # 避免除零：选择不在定义域边界的值
                test_values[sym] = random.uniform(1, 100)
            
            try:
                result1 = float(expr1.subs(test_values))
                result2 = float(expr2.subs(test_values))
                if abs(result1 - result2) < tolerance:
                    # 如果随机值相等，再测试几个值
                    for _ in range(3):
                        test_values = {sym: random.uniform(1, 100) for sym in symbols_in_expr}
                        result1 = float(expr1.subs(test_values))
                        result2 = float(expr2.subs(test_values))
                        if abs(result1 - result2) >= tolerance:
                            return False
                    return True
            except:
                pass
        
        return False
        
    except Exception as e:
        warnings.warn(f"Error comparing expressions '{expr1_str}' and '{expr2_str}': {e}")
        # 出错时回退到字符串比较
        return expr1_str == expr2_str


def improved_rough_equal(a, b, tolerance=0.500):
    """
    改进的rough_equal函数，支持数值和表达式比较
    
    这是对原有rough_equal函数的增强版本，可以处理：
    1. 纯数值比较（原有功能）
    2. 包含变量的表达式比较（新功能）
    
    Args:
        a: 第一个值（可以是数值或字符串表达式）
        b: 第二个值（可以是数值或字符串表达式）
        tolerance: 数值比较的容差（默认0.500，保持向后兼容）
    
    Returns:
        bool: 如果两个值相等返回True
    """
    # 处理None
    if a is None or b is None:
        return a == b
    
    # 如果都是数值，使用原有的rough_equal逻辑
    try:
        a_val = float(a)
        b_val = float(b)
        return abs(a_val - b_val) < tolerance
    except (ValueError, TypeError):
        pass
    
    # 如果至少有一个是字符串，尝试表达式比较
    a_str = str(a)
    b_str = str(b)
    
    return expressions_equal(a_str, b_str, tolerance=1e-10)


# 示例使用
if __name__ == "__main__":
    # 测试用例
    test_cases = [
        # 数值比较
        ("200", "200", True),
        ("125.3", "125.3", True),
        ("200", "200.0", True),
        
        # 表达式比较 - 等价形式
        ("5*(5*x+7)/(2*x+3)", "(25*x+35)/(2*x+3)", True),
        ("5*(5*x+7)/(2*x+3)", "5*(5*x+7)/(2*x+3)", True),
        ("x**3+12*x**2+48*x+64", "(x+4)**3", True),
        ("x**3+12*x**2+48*x+64", "x**3+12*x**2+48*x+64", True),
        
        # 表达式比较 - 不等价
        ("5*(5*x+7)/(2*x+3)", "5*x+7", False),
        ("x**3+12*x**2+48*x+64", "x**3", False),
        
        # 分数
        ("847/3", "847/3", True),
        ("847/3", "282.333", False),  # 近似值但不等价
        
        # 包含pi的表达式
        ("63*pi*x*x*x+66*pi*x*x+15*pi*x", "pi*x*(63*x**2+66*x+15)", True),
    ]
    
    print("Testing expression comparison:")
    for expr1, expr2, expected in test_cases:
        result = expressions_equal(expr1, expr2)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{expr1}' == '{expr2}': {result} (expected: {expected})")

