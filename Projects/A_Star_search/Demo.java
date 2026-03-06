import java.util.ArrayList;

public class Demo {

    public static void main(String[] args) {

        int[][] map = {
                {0, 0, 0, 0, 0},
                {0, 1, 1, 1, 0},
                {0, 0, 0, 1, 0},
                {0, 1, 0, 0, 0},
                {0, 0, 0, 0, 0}
        };

        int[] start = {0, 0};
        int[] goal  = {4, 4};

        ArrayList<Node> path = findPath(map, start, goal);

        if (path.size() == 0) {
            System.out.println("No path found!");
        } else {
            System.out.println("Path found, total steps " + (path.size() - 1) + " steps：");
            for (int i = 0; i < path.size(); i++) {
                System.out.print("[" + path.get(i).row + "," + path.get(i).col + "]");
                if (i < path.size() - 1) {
                    System.out.print(" -> ");
                }
            }
            System.out.println();
            printMap(map, path, start, goal);
        }
    }


    public static ArrayList<Node> findPath(int[][] map, int[] start, int[] goal) {

        ArrayList<Node> openList   = new ArrayList<>();
        ArrayList<Node> closedList = new ArrayList<>();

        Node startNode = new Node(start[0], start[1], null);
        startNode.g = 0;
        startNode.h = Math.abs(start[0] - goal[0]) + Math.abs(start[1] - goal[1]);
        startNode.f = startNode.g + startNode.h;
        openList.add(startNode);


        int[][] directions = { {-1, 0}, {1, 0}, {0, -1}, {0, 1} };

        while (openList.size() > 0) {

            Node current = openList.get(0);
            for (int i = 0; i < openList.size(); i++) {
                if (openList.get(i).f < current.f) {
                    current = openList.get(i);
                }
            }

            if (current.row == goal[0] && current.col == goal[1]) {
                return buildPath(current);
            }

            openList.remove(current);
            closedList.add(current);

            for (int i = 0; i < directions.length; i++) {
                int nextRow = current.row + directions[i][0];
                int nextCol = current.col + directions[i][1];


                if (nextRow < 0 || nextRow >= map.length)    continue;
                if (nextCol < 0 || nextCol >= map[0].length) continue;
                if (map[nextRow][nextCol] == 1) continue;
                if (isInList(closedList, nextRow, nextCol))  continue;

                Node neighbor = new Node(nextRow, nextCol, current);
                neighbor.g = current.g + 1;
                neighbor.h = Math.abs(nextRow - goal[0]) + Math.abs(nextCol - goal[1]);
                neighbor.f = neighbor.g + neighbor.h;

                if (!isInList(openList, nextRow, nextCol)) {
                    openList.add(neighbor);
                }
            }
        }

        return new ArrayList<>();
    }


    public static ArrayList<Node> buildPath(Node goalNode) {
        ArrayList<Node> path = new ArrayList<>();
        Node current = goalNode;
        while (current != null) {
            path.add(0, current);
            current = current.parent;
        }
        return path;
    }


    public static boolean isInList(ArrayList<Node> list, int row, int col) {
        for (int i = 0; i < list.size(); i++) {
            if (list.get(i).row == row && list.get(i).col == col) {
                return true;
            }
        }
        return false;
    }


    public static void printMap(int[][] map, ArrayList<Node> path, int[] start, int[] goal) {
        System.out.println();
        for (int row = 0; row < map.length; row++) {
            for (int col = 0; col < map[0].length; col++) {
                if (row == start[0] && col == start[1]) {
                    System.out.print("S ");
                } else if (row == goal[0] && col == goal[1]) {
                    System.out.print("G ");
                } else if (map[row][col] == 1) {
                    System.out.print("# ");
                } else if (isOnPath(path, row, col)) {
                    System.out.print("* ");
                } else {
                    System.out.print(". ");
                }
            }
            System.out.println();
        }
    }


    public static boolean isOnPath(ArrayList<Node> path, int row, int col) {
        for (int i = 0; i < path.size(); i++) {
            if (path.get(i).row == row && path.get(i).col == col) {
                return true;
            }
        }
        return false;
    }
}