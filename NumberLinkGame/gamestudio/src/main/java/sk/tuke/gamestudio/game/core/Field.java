package sk.tuke.gamestudio.game.core;

import java.awt.*;
import java.util.ArrayList;
import java.util.List;

public class Field {

    public static final int[][] LEVEL_ONE = {
            {3, 1, 1, 1, 2},
            {5, 1, 2, 5, 1},
            {1, 1, 1, 3, 1},
            {1, 1, 1, 1, 1},
            {4, 1, 1, 1, 4}
    };
    public static final int[][] LEVEL_TWO = {
            {3, 5, 1, 2, 1},
            {1, 1, 1, 4, 1},
            {4, 3, 1, 1, 1},
            {1, 5, 1, 1, 1},
            {1, 1, 1, 1, 2}
    };
    public static final int[][] LEVEL_THREE = {
            {3, 1, 1, 1, 1},
            {1, 1, 5, 1, 2},
            {1, 1, 4, 1, 4},
            {1, 2, 1, 5, 1},
            {1, 3, 1, 1, 1}
    };
    public static final int[][] LEVEL_FOUR = {
            {3, 1, 1, 4, 1},
            {1, 4, 1, 2, 1},
            {1, 1, 1, 1, 1},
            {1, 3, 2, 1, 1},
            {1, 1, 1, 1, 1}
    };

    public static final int[][] LEVEL_FIVE = {
            {1, 2, 1, 1, 1},
            {1, 3, 1, 2, 1},
            {1, 1, 1, 1, 1},
            {1, 3, 4, 1, 1},
            {1, 1, 1, 1, 4}
    };


    private int CurrentLevel;
    public List<int[][]> levels = new ArrayList<>();
    private GameState state;
    public Field(){
        levels.add(LEVEL_ONE);
        levels.add(LEVEL_TWO);
        levels.add(LEVEL_THREE);
        levels.add(LEVEL_FOUR);
        levels.add(LEVEL_FIVE);
        levels.add(LEVEL_FIVE);
        levels.add(LEVEL_FIVE);
    }
    public void setCurrentLevel(int CurrentLevel) {
        this.CurrentLevel = CurrentLevel;
    }
    public int getCurrentLevel(){
        return this.CurrentLevel;
    }
    public void setState(GameState state){
        this.state = state;
    }
    public GameState getState(){
        return this.state;
    }

    public void ShowLevel(){
        Color color = new Color(146, 132, 236, 74);
        Color color2 = new Color(54, 193, 243, 74);
        Color color3 = new Color(188, 69, 238, 74);
        Color color4 = new Color(66, 60, 131, 74);
        List<Color> colors = new ArrayList<>();
        colors.add(color);
        colors.add(color2);
        colors.add(color3);
        colors.add(color4);

        int i = 0;
        System.out.print("   ");
        for (; i < 5 ; i++){
            System.out.print(colorToString(colors.get(2)) +"["+ i + "]");
        }
        System.out.print("\n");
        i = 0;

        for (int[] ints : levels.get(CurrentLevel)) {
            System.out.print(colorToString(colors.get(2)) + "["+i+"]" );
            for (int anInt : ints) {
                System.out.print(" ");
                if (anInt >= 1) {
                    System.out.print(colorToString(colors.get(0)) + anInt );
                    System.out.print(" ");
                } else if(anInt == -1) {
                    System.out.print(colorToString(colors.get(0)) + "#" );
                    System.out.print(" ");
                }
                else {
                    System.out.print(colorToString(colors.get(3)) + "_");
                    System.out.print(" ");
                }
            }
            System.out.println();
            i++;
        }
    }

    private static String colorToString(Color color) {
        return String.format("\033[38;2;%d;%d;%dm", color.getRed(), color.getGreen(), color.getBlue());
    }
}




