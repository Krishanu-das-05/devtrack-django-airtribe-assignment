import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import CriticalIssue, Issue, LowPriorityIssue, Reporter
from .storage import read_records, write_records

REPORTERS_FILE = "reporters.json"
ISSUES_FILE = "issues.json"


def ping(request):
    return JsonResponse({"status": "ok"})


# ---------------------------------------------------------------- Reporters

@csrf_exempt
def reporters(request):
    if request.method == "POST":
        return create_reporter(request)
    if request.method == "GET":
        return get_reporters(request)
    return JsonResponse({"error": "Method not allowed"}, status=405)


def create_reporter(request):
    # 1. Turn the request body into a dict. Bad JSON → 400.
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    # 2. Check every required field is present. Missing → 400.
    for field in ["id", "name", "email", "team"]:
        if field not in data:
            return JsonResponse({"error": f"Missing field: {field}"}, status=400)

    # 3. Build the object and validate it. Invalid → 400.
    reporter = Reporter(data["id"], data["name"], data["email"], data["team"])
    try:
        reporter.validate()
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)

    # 4. Load the list, add the new one, save the list.
    records = read_records(REPORTERS_FILE)
    records.append(reporter.to_dict())
    write_records(REPORTERS_FILE, records)

    # 5. Return what was created, with 201 Created.
    return JsonResponse(reporter.to_dict(), status=201)


def get_reporters(request):
    records = read_records(REPORTERS_FILE)
    reporter_id = request.GET.get("id")

    # ?id= given → find that one reporter, or 404
    if reporter_id is not None:
        for record in records:
            if str(record["id"]) == reporter_id:
                return JsonResponse(record, status=200)
        return JsonResponse({"error": "Reporter not found"}, status=404)

    # No filter → return everyone
    return JsonResponse({"reporters": records})


# ------------------------------------------------------------------- Issues

@csrf_exempt
def issues(request):
    if request.method == "POST":
        return create_issue(request)
    if request.method == "GET":
        return get_issues(request)
    return JsonResponse({"error": "Method not allowed"}, status=405)


def create_issue(request):
    # 1. Turn the request body into a dict. Bad JSON → 400.
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    # 2. Check every required field is present. Missing → 400.
    for field in ["id", "title", "description", "status", "priority", "reporter_id"]:
        if field not in data:
            return JsonResponse({"error": f"Missing field: {field}"}, status=400)

    # 3. Pick the class from the priority, build the object, validate it.
    if data["priority"] == "critical":
        issue_class = CriticalIssue
    elif data["priority"] == "low":
        issue_class = LowPriorityIssue
    else:
        issue_class = Issue

    issue = issue_class(
        data["id"],
        data["title"],
        data["description"],
        data["status"],
        data["priority"],
        data["reporter_id"],
    )
    try:
        issue.validate()
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)

    # 4. Load the list, add the new one, save the list (without the message).
    records = read_records(ISSUES_FILE)
    records.append(issue.to_dict())
    write_records(ISSUES_FILE, records)

    # 5. Return what was created plus describe(), with 201 Created.
    response_data = issue.to_dict()
    response_data["message"] = issue.describe()
    return JsonResponse(response_data, status=201)


def get_issues(request):
    records = read_records(ISSUES_FILE)
    issue_id = request.GET.get("id")
    status = request.GET.get("status")

    # ?id= given → find that one issue, or 404
    if issue_id is not None:
        for record in records:
            if str(record["id"]) == issue_id:
                return JsonResponse(record, status=200)
        return JsonResponse({"error": "Issue not found"}, status=404)

    # ?status= given → only issues with that status
    if status is not None:
        matching = [record for record in records if record["status"] == status]
        return JsonResponse({"issues": matching})

    # No filter → return everything
    return JsonResponse({"issues": records})