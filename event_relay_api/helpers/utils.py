
def paginated_response(paginated_data, total_count):
    return { "data": paginated_data, "total": total_count }