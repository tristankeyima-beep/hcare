#!/usr/bin/env python3
from pathlib import Path


def _load_health_weekly_report_runner():
    source_path = Path(__file__).with_name("dify_aihcare_sport_runner.py")
    source = source_path.read_text(encoding="utf-8")
    replacements = (
        ("dify_aihcare_sport_runner.py", "dify_aihcare_health_weekly_report_runner.py"),
        ("dify-aihcare-sport-chatflow-test", "dify-aihcare-health-weekly-report-chatflow-test"),
        ("请根据基础档案生成运动方案。", "请根据基础档案生成健康周报。"),
        ('"sport"', '"report"'),
        ("sport", "health_weekly_report"),
        ("Sport", "HealthWeeklyReport"),
        ("SPORT", "HEALTH_WEEKLY_REPORT"),
        ("运动方案", "健康周报"),
        ("DIFY工程-AI干预方案-运动方案", "DIFY工程-AI干预方案-健康周报"),
        ("【入参】运动方案工作流测试入参.json", "【入参】健康周报工作流测试入参.json"),
        ("运动建议", "健康周报"),
        ("运动记录", "健康记录"),
        ("运动方式", "本周健康概览"),
        ('("有氧运动", ("有氧", "快走", "慢走", "骑行", "游泳"))', '("指标变化", ("指标", "血糖", "血压", "体重", "趋势", "异常"))'),
        ('("抗阻/力量训练", ("抗阻", "力量", "弹力带", "深蹲", "肌力"))', '("饮食执行", ("饮食", "早餐", "午餐", "晚餐", "外卖", "主食"))'),
        ('("碎片化执行", ("碎片", "分段", "拆成", "夜班", "忙碌"))', '("运动执行", ("运动", "快走", "散步", "时长", "疲劳", "不适"))'),
        ('("运动安全/停止条件", ("停止运动", "低血糖", "胸闷", "胸痛", "头晕", "不适"))', '("风险提醒", ("风险", "异常", "低血糖", "胸闷", "胸痛", "用药", "健管师"))'),
        ("有氧运动", "指标变化"),
        ("抗阻/力量训练", "饮食执行"),
        ("抗阻训练", "饮食执行"),
        ("碎片化执行", "运动执行"),
        ("柔韧/平衡", "下周关注"),
        ("运动安全/停止条件", "风险提醒"),
        ("有氧/抗阻/碎片/安全", "指标/饮食/运动/风险"),
        ("停止运动", "异常反馈"),
        ("近一年 exercise records", "近一年 health records"),
    )
    for old, new in replacements:
        source = source.replace(old, new)
    exec(compile(source, str(source_path), "exec"), globals())


_load_health_weekly_report_runner()
