// Node 类：代表地图上的一个格子
class Node {
    int row;
    int col;
    int g;
    int h;
    int f;        // f = g + h
    Node parent;

    Node(int row, int col, Node parent) {
        this.row = row;
        this.col = col;
        this.parent = parent;
    }
    //[1,0]
    //[3,4]
    //H=|1-4| + |0-4|
    //=3 + 4
    //=7
}