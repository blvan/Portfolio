package sk.tuke.gamestudio.server.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Scope;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.context.WebApplicationContext;
import sk.tuke.gamestudio.entity.Comment;
import sk.tuke.gamestudio.entity.Rating;
import sk.tuke.gamestudio.entity.Score;
import sk.tuke.gamestudio.game.core.Field;
import sk.tuke.gamestudio.game.core.GameState;
import sk.tuke.gamestudio.service.CommentService;
import sk.tuke.gamestudio.service.RatingService;
import sk.tuke.gamestudio.service.ScoreService;

import java.util.*;

@Controller
@RequestMapping("/numberlink")
@Scope(WebApplicationContext.SCOPE_SESSION)
//http://localhost:8080/mines/new
public class LineController {
    public LineController() {
        LevelsWin.add(LevelOneWin);
        LevelsWin.add(LevelTwoWin);
        LevelsWin.add(LevelThreeWin);
    }

    private Field field = new Field();

    private boolean marking;
    private int[][] Level(){
        return field.levels.get(field.getCurrentLevel());
    }

    @Autowired
    private ScoreService scoreService;
    @Autowired
    private CommentService commentService;
    @Autowired
    private RatingService ratingService;
    @Autowired
    private UserController userController;
    public List<Integer> SolvedNumber = new ArrayList<>();
    private List<String> route = new ArrayList<>();
    private List<String> move = new ArrayList<>();
    public List<Integer> ChosedNumber = new ArrayList<>();

    public static final int[][] LevelOneWin = {
            {3, 8, 7, 7, 2},
            {5, 8, 2, 5, 10},
            {10, 8, 8, 3, 10},
            {10, 10, 10, 10, 10},
            {4, 9, 9, 9, 4}
    };
    public static final int[][] LevelTwoWin = {
            {3, 5, 10, 2, 7},
            {8, 8, 10, 4, 7},
            {4, 3, 10, 9, 7},
            {9, 5, 10, 9, 7},
            {9, 9, 9, 9, 2}
    };

    public static final int[][] LevelThreeWin = {
            {3, 7, 7, 7, 7},
            {8, 7, 5, 10, 2},
            {8, 7, 4, 10, 4},
            {8, 2, 9, 5, 9},
            {8, 3, 9, 9, 9}
    };
    private final List<int[][]> LevelsWin = new ArrayList<>();
    private int pg = 0;

    @RequestMapping("/new")
    public String newGame(){
        ChosedNumber.clear();
        SolvedNumber.clear();

        field.levels.clear();
        field.levels.add(Field.LEVEL_ONE);
        field.setCurrentLevel(0);
        getHtmlField();
        return "new";
    }

    @RequestMapping("/rating")
    public String getRating(Model model){
        model.addAttribute("ratings",ratingService.getRatings("NumberLink"));
        return "rating";
    }

    @RequestMapping("/comment")
    public String getComment(Model model){
        model.addAttribute("comments",commentService.getComments("NumberLink"));
        return "comment";
    }
    @RequestMapping("/score")
    public String getScore(Model model){
        model.addAttribute("scores",scoreService.getTopScores("NumberLink"));
        return "score";
    }
    @RequestMapping("/rules")
    public String getRules(){
        return "rules";
    }
    @RequestMapping("/comment/add")
    public String setComment(String comment){
         commentService.addComment(new Comment("NumberLink",comment,userController.getLoggedUser().getLogin()));
        return "addComments";
    }

    @RequestMapping("/rating/add")
    public String setRating(){
        return "addRating";
    }

    @RequestMapping("/rating/add/rating")
    public String rating(@RequestParam(required = false) Integer rating, Model model) {
        ratingService.setRating(new Rating(userController.getLoggedUser().getLogin(),"NumberLink",rating));
        model.addAttribute("rating", ratingService.getAverageRating("NumberLink"));
        return "JSrating";
    }
    @RequestMapping("/JScomment")
    public String getJScom(){
        return "JScomment";
    }
    @RequestMapping("/JSscore")
    public String getJSscore(){
           return "JSscore";
    }
    @RequestMapping("/JSrating")
    public String getJSrating(){
        return "JSrating";
    }
    @RequestMapping
    public String numberlink(@RequestParam(required = false) Integer row, @RequestParam(required = false) Integer column) {

    if(row != null && column !=null ) {
            updateHTMLfield(row, column);
        }
        if (field.getState()== GameState.SOLVED){
            //..pg++;
            //cnnectedLines = 0;
            scoreService.addScore(new Score("NumberLink", userController.getLoggedUser().getLogin(), 40,new Date()));
        }
        return "numberlink";
    }

    public static boolean checkNumberlinkPaths(int[][] level,int number) {
        int currentNumber = 1;

        for (int row = 0; row < level.length; row++) {
            for (int col = 0; col < level[row].length; col++) {
                if (level[row][col] == currentNumber) {
                    boolean[][] visited = new boolean[level.length][level[0].length];
                    boolean isConnected = CheckConnetion(level, row, col, currentNumber, visited);
                    if (!isConnected) {
                        return false;
                    }
                    currentNumber++;
                }
            }
        }

        return true;
    }

    public static boolean CheckConnetion(int[][] level, int row, int col, int currentNumber, boolean[][] visited) {
        if (row < 0 || row >= level.length || col < 0 || col >= level[row].length || level[row][col] != currentNumber || visited[row][col]) {
            return false;
        }

        visited[row][col] = true;

        boolean isConnected = CheckConnetion(level, row - 1, col, currentNumber, visited) // hore
                || CheckConnetion(level, row + 1, col, currentNumber, visited) // niz
                || CheckConnetion(level, row, col - 1, currentNumber, visited) // vlavo
                || CheckConnetion(level, row, col + 1, currentNumber, visited); // vpravo

        return isConnected;
    }

    public String updateHTMLfield(int row, int column){
        field.setState(GameState.PLAYING);
        int number = Level()[row][column];
        ChosedNumber.add(1);
        if(number!=1 && number <=5){
            ChosedNumber.clear();
            ChosedNumber.add(number);
        }else {
            if (ChosedNumber.get(0) >= 2 && ChosedNumber.get(0) <= 5) {
                Level()[row][column] = ChosedNumber.get(0) + 5;
            }
        }

        boolean isCorrect = checkNumberlinkPaths(field.levels.get(field.getCurrentLevel()),ChosedNumber.get(0) + 5);
        System.out.println("Paths are connected: " + isCorrect);
        int correctConnections = countCorrectConnections(field.levels.get(field.getCurrentLevel()),LevelOneWin) - 8;
        System.out.println("Number of correct connections: " + correctConnections);
        if(isCorrect){
           // compareLevelOneArrays(field.levels.get(field.getCurrentLevel()),LevelOneWin);
            //printMatrix(field.levels.get(field.getCurrentLevel()));
            System.out.println("Paths are connected correctly: " + compareLevelOneArrays(field.levels.get(field.getCurrentLevel()),LevelsWin.get(pg)));
            if ( compareLevelOneArrays(field.levels.get(field.getCurrentLevel()),LevelsWin.get(pg))){
                pg++;
                field.setState(GameState.SOLVED);
                field.setCurrentLevel(pg);
            }
        }



        return "numberlink";
    }

    public static int countCorrectConnections(int[][] level, int[][] solution) {
        int rows = level.length;
        int cols = level[0].length;
        int count = 0;

        for (int row = 0; row < rows; row++) {
            for (int col = 0; col < cols; col++) {
                int currentNumber = level[row][col];
                int connectedNumber = solution[row][col];

                if (currentNumber > 0 && connectedNumber == currentNumber) {
                    count++;
                }
            }
        }
        return count;
    }


    public boolean compareLevelOneArrays(int[][] array1, int[][] array2){
        if (array1.length != array2.length || array1[0].length != array2[0].length) {
            return false;
        }

        for (int i = 0; i < array1.length; i++) {
            for (int j = 0; j < array1[i].length; j++) {
                if (array1[i][j] != array2[i][j]) {
                    return false;
                }
            }
        }

        return true;
    }

    public static void printMatrix(int[][] matrix) {
        for (int i = 0; i < matrix.length; i++) {
            for (int j = 0; j < matrix[i].length; j++) {
                System.out.print(matrix[i][j] + " ");
            }
            System.out.println();
        }
    }
    public String getHtmlField(){
        route.add("<img src='/images/route/first.png'>\n");
        route.add("<img src='/images/route/second.png'>\n");
        route.add("<img src='/images/route/third.png'>\n");
        route.add("<img src='/images/route/fours.png'>\n");

        //check for previous position and cant move more than on one
        Integer row = 0;Integer column = 0;
        StringBuilder sb = new StringBuilder();
        sb.append("<table>\n");
        sb.append("<img src='/images/title.png'>\n");
        for (int[] ints : field.levels.get(field.getCurrentLevel())) {
            sb.append("<tr>\n");
            for (int anInt : ints) {
                sb.append("<td>\n");
                sb.append("<a href='/numberlink?row=" + row + "&column=" + column + "'>\n");
                switch (anInt) {
                    case 1 -> sb.append("<img src='/images/numbers/zero.png'>\n");
                    case 2 -> sb.append("<img src='/images/numbers/one.png'>\n");
                    case 3 -> sb.append("<img src='/images/numbers/two.png'>\n");
                    case 4 -> sb.append("<img src='/images/numbers/three.png'>\n");
                    case 5 -> sb.append("<img src='/images/numbers/four.png'>\n");

                    case 7 -> sb.append(route.get(0));
                    case 8 -> sb.append(route.get(1));
                    case 9 -> sb.append(route.get(2));
                    case 10 -> sb.append(route.get(3));
                }
                if(column !=4)
                column++;
                else column=0;
                sb.append("</td>\n");
            }
            row++;
            sb.append("</tr>\n");
        }
        sb.append("</table>\n");
    return sb.toString();
    }
}
