extends Reference
# Team soldiers prefer uncaptured posts and change goals as flags flip.
static func choose_post(posts, team, origin):
    var best = -1
    var closest = INF
    for i in range(posts.size()):
        if abs(posts[i]["progress"]) >= 99.99 and (posts[i]["progress"] > 0.0) == (team == 0):
            continue
        var distance = origin.distance_to(posts[i]["node"].translation)
        if distance < closest:
            closest = distance
            best = i
    return best
