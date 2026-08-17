from rest_framework.response import Response


def success_response(
    message,
    data=None,
    status_code=200,
):
    return Response(
        {
            "success": True,
            "message": message,
            "data": data,
        },
        status=status_code,
    )


def error_response(
    message,
    error_code,
    status_code=400,
    data=None,
):
    return Response(
        {
            "success": False,
            "message": message,
            "error_code": error_code,
            "data": data,
        },
        status=status_code,
    )