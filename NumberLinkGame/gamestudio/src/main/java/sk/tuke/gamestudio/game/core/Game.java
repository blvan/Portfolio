package sk.tuke.gamestudio.game.core;

import org.springframework.beans.factory.annotation.Autowired;
import sk.tuke.gamestudio.entity.Score;
import sk.tuke.gamestudio.service.ScoreService;
import sk.tuke.gamestudio.service.ScoreServiceJDBC;
import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.Id;
import java.util.*;

public class Game {
    private Field field = new Field();
    private int number;
    public List<Integer> SolvedNumber = new ArrayList<>();
    private Player player = new Player(0, 0);
    private int[][] Level(){
       return field.levels.get(field.getCurrentLevel());
    }
    private  Scanner scanner1 = new Scanner(System.in);
    private  ScoreServiceJDBC scoreServiceJDBC = new ScoreServiceJDBC();

    // @Autowired
    private ScoreService scoreService;
    private void Input(){
        Scanner scanner = new Scanner(System.in);
        while (true) {
            int x;
            int y;
            while (true) {
                try {
                    x = scanner.nextInt();
                    y = scanner.nextInt();
                    break;
                } catch (InputMismatchException e) {
                    System.out.println("Invalid input. Please enter two integers.");
                    scanner.nextLine();
                }
            }
            player.newPlayer(x, y);
            number = Level()[x][y];
            boolean trigger = false;
            if (number >=1) {
                for (Integer num : SolvedNumber) {
                    if (num == number) {
                        System.out.println("You already used this number!\n Enter two numbers:");
                        trigger = true;
                    }
                }
                if (!trigger) {
                    break;
                }
            }
            else if (number == -1 || number == 0) {
                System.out.println("You can't start from here!\n Enter two numbers:");
            }
            else{
                break;
            }
        }
    }


    public void update() {
        boolean solved;
        for (int h = 0; h < 1; h++){
            System.out.println("Enter two numbers [column][row] of the number: ");
            Input();
            int moveCounter = 0;
            int Lives = 2;
            solved = false;
            do {
                System.out.print("Number is "+ number + ":\n");
                System.out.print("You can make " + Lives + " incorrect move(s).\n");
                field.ShowLevel();
                field.setState(GameState.PLAYING);
                System.out.print("Enter move (up, down, left, right): ");
                String input = scanner1.nextLine().toLowerCase();
                switch (input) {
                    case "up" -> player.moveUp();
                    case "down" -> player.moveDown();
                    case "left" -> player.moveLeft();
                    case "right" -> player.moveRight();
                    default -> System.out.println("Invalid move!");
                }
                for (int i = 0; i < Level().length; i++) {
                    if (Lives == 0){
                        Scanner sw = new Scanner(System.in);
                        int width = 20;
                        System.out.println("You have LOST!");
                        System.out.printf("%-" + width/2 + "s%s%"+ (width - width/2) +"s", "", "\n", "");
                        System.out.printf("%-" + width/2 + "s%s%"+ (width - width/2) +"s", "", "[1]Score\n", "");
                        System.out.printf("%-" + width/2 + "s%s%"+ (width - width/2) +"s", "", "[2]Exit\n", "");
                        int b = sw.nextInt();
                        switch (b){
                            case 1:ShowScore(scoreServiceJDBC);
                            case 2:System.exit(0);
                        }
                        break;
                    }
                    if ((player.getX() <= 4 && player.getX() >= 0) && (player.getY() <= 4 && player.getY() >= 0)) {
                    for (int j = 0; j < Level().length; j++) {
                        if (i == player.getX() && j == player.getY()) {
                            if (Level()[i][j] == 0) {
                                Level()[i][j] = -1;
                                moveCounter += 1;
                            }
                            else if (Level()[i][j] >= 0 && Level()[i][j] == number && moveCounter >= 2) { //&& i != x
                                field.setState(GameState.SOLVED);
                            } else {
                                Lives = wrongMove(Lives, input);
                                break;
                            }
                        }
                      }
                    }
                    else {
                        Lives = wrongMove(Lives, input);
                        break;
                    }
                }
                if (field.getState() == GameState.SOLVED) {
                    SolvedNumber.add(number);
                    System.out.println("Done!");
                    solved = true;
                }
            }while (!solved);
        }
        SolvedNumber.clear();
        newLevel(field);
        scoreService.addScore(new Score("NumberLink","Player",30,new Date()));

        update();
    }

    private void ShowScore(ScoreServiceJDBC scoreServiceJDBC){
        List<Score> scores = scoreServiceJDBC.getTopScores("NumberLink");
        System.out.println("-----------");
        System.out.println("|Points: "+ scores.get(0) +"|");
        System.out.println("-----------");
        System.out.println("\n");
    }

    public static void newLevel(Field field) {
        int Level = field.getCurrentLevel() + 1;
        int CurrentLevel = Level + 1;
        System.out.println("You finished Level:" + Level);
        field.setCurrentLevel(Level);
        System.out.println("Current Level:" + CurrentLevel);
        field.ShowLevel();
        System.out.print("Choose the number from which you would like to start playing...\n");
    }

    private int wrongMove(int lives, String input) {
        System.out.println("You cant move here!");
        lives -= 1;
        switch (input) {
            case "up" -> player.moveDown();
            case "down" -> player.moveUp();
            case "left" -> player.moveRight();
            case "right" -> player.moveLeft();
        }
        return lives;
    }
}
