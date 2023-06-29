package sk.tuke.gamestudio.game.core;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

public class PlayerTest {

    private Player player;
    private int initialX;
    private int initialY;

    @BeforeEach
    public void setUp() {
        initialX = 0;
        initialY = 0;
        player = new Player(initialX, initialY);
    }

    @Test
    public void testNewPlayer() {
        int newX = 2;
        int newY = 5;
        player.newPlayer(newX, newY);
        assertEquals(newX, player.getX(), "Player's X position was not updated correctly.");
        assertEquals(newY, player.getY(), "Player's Y position was not updated correctly.");
    }

    @Test
    public void testMoveUp() {
        player.moveUp();
        assertEquals(initialX - 1, player.getX(), "Player did not move up correctly.");
        assertEquals(initialY, player.getY(), "Player's Y position should not have changed when moving up.");
    }

    @Test
    public void testMoveDown() {
        player.moveDown();
        assertEquals(initialX + 1, player.getX(), "Player did not move down correctly.");
        assertEquals(initialY, player.getY(), "Player's Y position should not have changed when moving down.");
    }

    @Test
    public void testMoveLeft() {
        player.moveLeft();
        assertEquals(initialX, player.getX(), "Player's X position should not have changed when moving left.");
        assertEquals(initialY - 1, player.getY(), "Player did not move left correctly.");
    }

    @Test
    public void testMoveRight() {
        player.moveRight();
        assertEquals(initialX, player.getX(), "Player's X position should not have changed when moving right.");
        assertEquals(initialY + 1, player.getY(), "Player did not move right correctly.");
    }

}