import logging

log = logging.getLogger(__name__)

def unwrap_branch(branch):
    if isinstance(branch, list) and len(branch) == 1:
        return branch[0]
    return branch
