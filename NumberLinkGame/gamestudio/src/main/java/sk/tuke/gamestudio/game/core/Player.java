package sk.tuke.gamestudio.game.core;

public class Player {
    private int x;
    private int y;

    public Player(int x, int y) {
        this.x = x;
        this.y = y;
    }
    public void newPlayer(int x, int y) {
        this.x = x;
        this.y = y;
    }
    public void moveUp() {
        x--;
    }

    public void moveDown() {
        x++;
    }

    public void moveLeft() {
        y--;
    }

    public void moveRight() {
        y++;
    }

    public int getX() {
        return x;
    }

    public int getY() {
        return y;
    }
}