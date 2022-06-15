#!/usr/local/cs/bin/python3

import zlib
import sys
import os


class CommitNode:
    def __init__(self, commit_hash, branches=[]):
        self.commit_hash = commit_hash
        self.parents = set()
        self.children = set()
        self.branches = branches


# top-level function
def topo_order_commits():
    branch_commitid = get_localbranch_name()
    # build two graph original and commit since dict() only does shallow copy
    # and generate_ordered_commit needs to modify the commit graph
    # keep the original graph for show_commits to use
    original_graph = build_original_graph(branch_commitid)
    root_commits, commit_graph = build_commit_graph(branch_commitid)
    ordered_commits = generate_ordered_commit(root_commits, commit_graph)
    show_commits(ordered_commits, original_graph)
    

# Step 1: Discover the .git directory
def discover_git_dir():
    while (os.getcwd() != '/'):
        if (os.path.isdir(os.getcwd() + '/.git')):
            return os.path.join(os.getcwd(), '.git')
        os.chdir('../')
    print("Not inside a Git repository", file=sys.stderr)
    exit(1)


# Step 2: Get the list of local branch names
def get_localbranch_name():
    git_dir = os.path.join(discover_git_dir(), 'refs', 'heads')
    branch_commitid = dict()
    for root, dirs, files in os.walk(git_dir, topdown=True):
        for name in files:
            commitid = open((os.path.join(root, name)), 'r').read()[:-1]
            branch_dir_name = os.path.join(root[len(git_dir)+1:], name)
            if commitid not in branch_commitid.keys():
                branch_commitid[commitid] = [branch_dir_name]
            else:
                branch_commitid[commitid].append(branch_dir_name)
    return branch_commitid


# Step 3: Build the original graph
def build_original_graph(branch_commitid):
    original_graph = dict()
    stack = []
    path = os.path.join((os.path.join(discover_git_dir(), 'objects')))
    # add all branches to the stack
    for hashid in branch_commitid:
        stack.append(hashid)

    # add all hash to the graph
    while True:
        hashid = stack.pop()
        hash_path = os.path.join(path, hashid[:2], hashid[2:])
        compressed = open(hash_path, 'rb').read()
        contents = zlib.decompress(compressed).decode()

        while (contents.find('\nparent') > -1):
            con = contents.find('\nparent')
            parent = contents[con+8:con+48]
            if parent not in stack:
                stack.append(parent)

            if hashid not in original_graph.keys():
                original_graph[hashid] = \
                        CommitNode(hashid, branch_commitid[hashid])

            original_graph[hashid].parents.add(parent)

            if parent not in original_graph.keys():
                if parent in branch_commitid.keys():
                    original_graph[parent] = \
                            CommitNode(parent, branch_commitid[parent])
                else:
                    original_graph[parent] = CommitNode(parent)

            original_graph[parent].children.add(hashid)
            contents = contents[contents.find('\nparent') + 48:]

        if (len(stack) == 0):
            break

    return original_graph


# Step 3: Build the commit graph
def build_commit_graph(branch_commitid):
    commit_graph = dict()
    root_commit = []
    stack = []
    path = os.path.join((os.path.join(discover_git_dir(), 'objects')))
    # add all branches to the stack
    for hashid in branch_commitid:
        stack.append(hashid)

    # add all hash to the graph
    while True:
        hashid = stack.pop()
        hash_path = os.path.join(path, hashid[:2], hashid[2:])
        compressed = open(hash_path, 'rb').read()
        contents = zlib.decompress(compressed).decode()

        while (contents.find('\nparent') > -1):
            con = contents.find('\nparent')
            parent = contents[con+8:con+48]
            if parent not in stack:
                stack.append(parent)

            if hashid not in commit_graph.keys():
                commit_graph[hashid] = \
                        CommitNode(hashid, branch_commitid[hashid])

            commit_graph[hashid].parents.add(parent)

            if parent not in commit_graph.keys():
                if parent in branch_commitid.keys():
                    commit_graph[parent] = \
                            CommitNode(parent, branch_commitid[parent])
                else:
                    commit_graph[parent] = CommitNode(parent)

            commit_graph[parent].children.add(hashid)
            contents = contents[contents.find('\nparent') + 48:]

        if (len(stack) == 0):
            break

    for node in commit_graph:
        if (len(commit_graph[node].parents) == 0):
            root_commit.append(node)

    # for node in commit_graph:
    #     print('\n')
    #     print('hashid:', node)
    #     print('parents:', commit_graph[node].parents)
    #     print('children:', commit_graph[node].children)
    #     print('branches:', commit_graph[node].branches)

    return root_commit, commit_graph


# Step 4: Generate a topological ordering of the commits in the graph
def generate_ordered_commit(root_commits, private_graph):
    order_commit = []
    roots = []

    for root in root_commits:
        roots.append(root)

    while True:
        commit = roots.pop(0)
        order_commit.append(commit)

        for child in private_graph[commit].children:
            private_graph[child].parents.remove(commit)
            if (len(private_graph[child].parents) == 0):
                roots.append(child)

        if (len(roots) == 0):
            break

    order_commit.reverse()

    return order_commit


# Step 5: Print the commit hashes in the order generated by the previous step
#         from the least to the greatest
def show_commits(ordered_commits, commit_graph):
    for i in range(len(ordered_commits)):
        node = commit_graph[ordered_commits[i]]

        if len(node.branches) == 0:
            print(ordered_commits[i])
        else:
            print(ordered_commits[i] + " ", end="")
            print(*sorted(node.branches))

        if i < (len(ordered_commits) - 1):
            next_node = commit_graph[ordered_commits[i + 1]]
            if ordered_commits[i + 1] not in node.parents:
                print(*[parent for parent in node.parents], end="=\n\n=")
                print(*[child for child in next_node.children])


if __name__ == '__main__':
    topo_order_commits()
