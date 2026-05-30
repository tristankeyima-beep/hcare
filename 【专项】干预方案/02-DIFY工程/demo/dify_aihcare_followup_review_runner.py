#!/usr/bin/env python3
from pathlib import Path


def _load_followup_review_runner():
    source_path = Path(__file__).with_name("dify_aihcare_sport_runner.py")
    source = source_path.read_text(encoding="utf-8")
    replacements = (
        ("dify_aihcare_sport_runner.py", "dify_aihcare_followup_review_runner.py"),
        ("dify-aihcare-sport-chatflow-test", "dify-aihcare-followup-review-chatflow-test"),
        ("请根据基础档案生成运动方案。", "请根据基础档案生成复诊复查指导。"),
        ('"sport"', '"followup_review"'),
        ("sport", "followup_review"),
        ("Sport", "FollowupReview"),
        ("SPORT", "FOLLOWUP_REVIEW"),
        ("运动方案", "复诊复查指导"),
        ("DIFY工程-AI干预方案-运动方案", "DIFY工程-AI干预方案-复诊复查指导"),
        ("【入参】运动方案工作流测试入参.json", "【入参】复诊复查指导工作流测试入参.json"),
        ("运动建议", "复诊复查指导"),
        ("运动记录", "随访记录"),
        ("运动方式", "复诊准备"),
        ('("有氧运动", ("有氧", "快走", "慢走", "骑行", "游泳"))', '("复查项目", ("复查", "检查", "糖化", "血糖", "血脂", "肝肾", "尿微量", "血压"))'),
        ('("抗阻/力量训练", ("抗阻", "力量", "弹力带", "深蹲", "肌力"))', '("异常就医触发", ("异常", "就医", "低血糖", "胸闷", "胸痛", "头晕", "破溃"))'),
        ('("碎片化执行", ("碎片", "分段", "拆成", "夜班", "忙碌"))', '("资料准备", ("资料", "记录", "清单", "检查单", "用药", "日志"))'),
        ('("运动安全/停止条件", ("停止运动", "低血糖", "胸闷", "胸痛", "头晕", "不适"))', '("结果回传", ("回传", "反馈", "复诊", "医生", "健管师", "随访"))'),
        ("有氧运动", "复查项目"),
        ("抗阻/力量训练", "异常就医触发"),
        ("抗阻训练", "异常触发"),
        ("碎片化执行", "资料准备"),
        ("柔韧/平衡", "结果回传"),
        ("运动安全/停止条件", "提前就医触发"),
        ("有氧/抗阻/碎片/安全", "复诊时间/复查项目/异常触发/资料准备"),
        ("停止运动", "提前就医"),
        ("近一年 exercise records", "近一年 followup records"),
    )
    for old, new in replacements:
        source = source.replace(old, new)
    exec(compile(source, str(source_path), "exec"), globals())


_load_followup_review_runner()
