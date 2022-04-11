"""
"""

import json

JSON_PLANS = '''
[{"args": [],
    "item_type": "plan",
    "item_uid": "5f3c7382-1af5-4ccf-a2e3-cb83871b7343",
    "kwargs": {},
    "name": "open_shutter",
    "user": "GUI Client",
    "user_group": "admin"},
   {"args": [],
    "item_type": "plan",
    "item_uid": "0da3a953-9163-4f28-b12c-83418f6103a0",
    "kwargs": {},
    "name": "prime_hdf_plugin",
    "user": "GUI Client",
    "user_group": "admin"},
   {"args": [],
    "item_type": "plan",
    "item_uid": "738294fc-8921-4184-a19c-df7ffb754505",
    "kwargs": {"time": 2},
    "name": "sleep",
    "user": "GUI Client",
    "user_group": "admin"},
   {"args": [],
    "item_type": "plan",
    "item_uid": "bc613c4f-46d2-4d81-9003-67e1fbb9f75f",
    "kwargs": {"x": 0, "y": 0},
    "name": "move_fine_positioner",
    "user": "GUI Client",
    "user_group": "admin"},
   {"args": [],
    "item_type": "plan",
    "item_uid": "511b6392-ea45-4729-a098-f44de2c9bfcd",
    "kwargs": {"coarse_gain": 0, "fine_gain": 1, "noise": 0},
    "name": "game_configure",
    "user": "GUI Client",
    "user_group": "admin"},
   {"args": [],
    "item_type": "plan",
    "item_uid": "23cf69ca-50e4-4821-a218-45e39c62ca2e",
    "kwargs": {"atime": 0.01},
    "name": "take_image",
    "user": "GUI Client",
    "user_group": "admin"}]
'''


def main():
    q = json.loads(JSON_PLANS)
    for plan in q:
        spec = plan["name"]
        if len(plan["args"]) > 0:
            spec += " "
            spec += " ".join(plan["args"])
        if len(plan["kwargs"]) > 0:
            for k, v in plan["kwargs"].items():
                spec += f" {k}={v}"
        # print(spec)
        plan.pop("item_type")
        plan.pop("item_uid")
        plan.pop("user")
        plan.pop("user_group")
        print(json.dumps(plan))
        """
        qserver queue add plan
        '{
            "name": "take_image",
            "args": [.5],
            "kwargs": {"md": {"task": "use the qserver"}}
        }'
        """


def plan_dict(plan, *args, **kwargs):
    d = dict(name=plan)
    if len(args):
        d["args"] = args
    if len(kwargs):
        d["kwargs"] = kwargs
    return d


def example():
    plans = [
        plan_dict("prime_hdf_plugin"),
        plan_dict("move_fine_positioner", 0, 0),
        plan_dict("new_sample", 0, 1, 0),
        plan_dict("open_shutter"),
        plan_dict("take_image", 0.01, 0.2),
        plan_dict("sleep", 5),
        plan_dict("close_shutter"),
        plan_dict("take_image", atime=0.01, aperiod=0.2),
        plan_dict("move_fine_positioner", -371.016, -215.053),
        plan_dict("take_image", atime=0.01, aperiod=0.2),
    ]
    print_plan_commands(plans)


def print_plan_commands(plans):
    for plan in plans:
        txt = json.dumps(plan)
        print(f"qserver queue add plan '{txt}'")


if __name__ == "__main__":
    # main()
    example()
