package sk.tuke.gamestudio.game.consoleui;

import sk.tuke.gamestudio.entity.Comment;
import sk.tuke.gamestudio.entity.Rating;
import sk.tuke.gamestudio.game.core.Field;
import sk.tuke.gamestudio.game.core.Game;
import sk.tuke.gamestudio.entity.Score;
import sk.tuke.gamestudio.service.*;

import java.awt.*;

import java.util.List;
import java.util.Scanner;

public class ConsoleUI {
    private Rating rating;
    private RatingServiceJPA ratingServiceJPA;
    private RatingServiceJDBC ratingServiceJDBC;

    private ScoreService scoreService;

    private CommentService commentService;

    private RatingService ratingService;
    public String PlayerName;
    private Scanner scanner = new Scanner(System.in);
    private Color color = new Color(146, 132, 236, 74);
    public void play() {
        Field field = new Field();
        int width = 20;
      while (true) {
          System.out.printf(colorToString(color) + "%-" + width/2 + "s%s%"+ (width - width/2) +"s", "", "Welcome to the game NumberLink!\n", "");
          System.out.printf("%-" + width/2 + "s%s%"+ (width - width/2) +"s", "", "What is your name?\n", "");
            Input();
          System.out.printf("%-" + width/2 + "s%s%"+ (width - width/2) +"s", "", "\n", "");
          System.out.printf("%-" + width/2 + "s%s%"+ (width - width/2) +"s", "", "[1]Play\n", "");
          System.out.printf("%-" + width/2 + "s%s%"+ (width - width/2) +"s", "", "[2]Rules\n", "");
          System.out.printf("%-" + width/2 + "s%s%"+ (width - width/2) +"s", "", "[3]Score\n", "");
          System.out.printf("%-" + width/2 + "s%s%"+ (width - width/2) +"s", "", "[4]Rating\n", "");
          System.out.printf("%-" + width/2 + "s%s%"+ (width - width/2) +"s", "", "[5]Comment\n", "");
          System.out.printf("%-" + width/2 + "s%s%"+ (width - width/2) +"s", "", "[6]Exit\n", "");
          int x = scanner.nextInt();
          switch (x){
              case 1: startLevel(field);
              case 2:System.out.print("The task is to connect all pairs of numbers on\nthe board by marking the route from the number to its pair.\nAt the end, there must not be an unfilled space on the playing field.\nRoutes connecting numbers must not overlap and a route can only be one box wide.\n");
                  System.out.printf("%-" + width/2 + "s%s%"+ (width - width/2) +"s", "", "\n", "");
                  System.out.printf("%-" + width/2 + "s%s%"+ (width - width/2) +"s", "", "[1]Play\n", "");
                  System.out.printf("%-" + width/2 + "s%s%"+ (width - width/2) +"s", "", "[2]Exit\n", "");
              int b = scanner.nextInt();
                  switch (b){
                      case 1: startLevel(field);
                      case 2:return;
                            }
                            case 3: ShowTable(scoreService);break;
                            case 4: rating.setRating(4);
                                    Rating(rating);
                                    break;
                            case 5:    Comment(commentService);break;
                 case 6: return;
              default: System.out.println("Invalid number!");
          }
      }
    }

    private void Comment(CommentService comment){

        if (comment != null) {
            List<Comment> comments = comment.getComments("NumberLink");
            System.out.println("-------------------------------------------------------------------------");
            for (Comment comment1 : comments) {
                System.out.println("|Game: " + comment1.getGame() + "|Player: " + comment1.getPlayer() + " |Comment: " + comment1.getComment() + "|");
            }
            System.out.println("-------------------------------------------------------------------------");
        }else {
            System.out.println("-----");
            System.out.println("|None|");
            System.out.println("-----");
        }
    }
    private void Rating(Rating rating){
        ratingServiceJPA.setRating(rating);
        /*if (rating != null) {
            List<Rating> ratings = rating.getRatings("NumberLink");
            System.out.println("-------------------------------------------------------------------------");
            for (Rating rating1 : ratings) {
                System.out.println("|Game: " + rating1.getGame() + "|Player: " + rating1.getPlayer() + " |Points: " + rating1.getRating() + "|");
            }
            System.out.println("-------------------------------------------------------------------------");
        }else {
            System.out.println("-----");
            System.out.println("|None|");
            System.out.println("-----");
        }*/
    }
    private void ShowTable(ScoreService scoreService){
        if (scoreService != null) {
            List<Score> scores = scoreService.getTopScores("NumberLink");
            System.out.println("-------------------------------------------------------------------------");
            for (Score score : scores) {
                System.out.println("|Game: " + score.getGame() + "|Player: " + score.getPlayer() + " |Points: " + score.getPoints() + " |Time: " + score.getPlayedOn() + "|"+ score.getIdent()+ "|");
            }
            System.out.println("-------------------------------------------------------------------------");
        }else {
            System.out.println("-----");
            System.out.println("|None|");
            System.out.println("-----");
        }
    }
    private void startLevel(Field field){
        int Level = field.getCurrentLevel() +1;
        System.out.print("Level  "+ Level + ":\n");
        field.ShowLevel();
        System.out.print("Choose the number from which you would like to start playing...\n");
        Game game = new Game();
        game.update();
    }
    private static String colorToString(Color color) {
        return String.format("\033[38;2;%d;%d;%dm", color.getRed(), color.getGreen(), color.getBlue());
    }


    private void Input(){
        Scanner scanner = new Scanner(System.in);
        PlayerName = scanner.nextLine();
    }

}
