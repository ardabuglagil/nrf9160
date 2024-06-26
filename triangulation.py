import numpy as np
import matplotlib.pyplot as plt

def triangulate(points_np, signal_strengths_np, sigma_np):
    total_strength = np.sum(signal_strengths_np)
    weights = signal_strengths_np / total_strength
    std = np.sqrt(np.sum(np.square(weights) * sigma_np))
    position = np.sum(points_np * weights, axis=1)
    # position = np.expand_dims(position, axis=1)
    return position, std




def multilateration(s, P):
    anchor_num = P.shape[1]
    dimension_num = P.shape[0]

    #multilateration algorithm doesn't work for 2 anchor positions, average of the anchors is calculated instead
    if anchor_num == 2:
        direction_vec = P[:, 1] - P[:, 0]
        direction_vec /= np.linalg.norm(direction_vec)

        p0 = P[:, 0] + s[0] * direction_vec
        p1 = P[:, 1] - s[1] * direction_vec


        average_point = (p0 + p1) / 2
        return np.array([np.linalg.norm(average_point)**2,  average_point[0], average_point[1]])


    if dimension_num == 2:
        A = np.zeros((anchor_num, 3))
        b = np.zeros((anchor_num, 1))

        for i in range(anchor_num):
            A[i, :] = np.array([[1, -2 * P[0, i], -2 * P[1, i]]])
            b[i, :] = np.array([[s[i] ** 2 - P[0, i] ** 2 - P[1, i] ** 2]])

        x = np.linalg.inv(A.T @ A) @ A.T @ b
        return x
    elif dimension_num == 3:
        A = np.zeros((anchor_num, 4))
        b = np.zeros((anchor_num, 1))

        for i in range(anchor_num):
            A[i, :] = np.array([[1, -2 * P[0, i], -2 * P[1, i], -2 * P[2, i]]])
            b[i, :] = np.array([[s[i, :] ** 2 - P[0, i] ** 2 - P[1, i] ** 2 - P[2, i] ** 2]])

        x = np.linalg.inv(A.T @ A) @ A.T @ b
        return x

def test_triangulate():
    points = np.array([[1, 7, 1],
                       [2, 5, 6]])

    signal_strengths = np.array([20, 70, 30])
    pos = triangulate(points, signal_strengths)
    print(pos)

    plt.scatter(points[0, :], points[1, :], alpha=0.5)
    plt.scatter(pos[0], pos[1], c=2)
    for i, txt in enumerate(signal_strengths):
        plt.annotate("Strength: {}".format(txt), (points[0, i], points[1, i]))
    plt.annotate("Combined position", pos)
    plt.title("Triangulation of position based on signal strengths")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.show()


# test_triangulate()
