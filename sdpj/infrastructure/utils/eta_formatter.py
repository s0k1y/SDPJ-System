def format_eta(seconds: float) -> str:
    if seconds < 0:
        return "计算中..."
    if seconds < 60:
        return f"{int(seconds)}秒"
    if seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}分{secs}秒"
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    return f"{hours}小时{minutes}分"
