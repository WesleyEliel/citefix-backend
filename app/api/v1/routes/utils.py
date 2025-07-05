def response_helper(response):
    return {"_id": response.id, **response.dict()}
