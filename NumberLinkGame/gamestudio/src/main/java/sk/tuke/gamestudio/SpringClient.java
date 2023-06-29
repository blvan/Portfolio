package sk.tuke.gamestudio;

import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.WebApplicationType;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.domain.EntityScan;
import org.springframework.boot.builder.SpringApplicationBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.FilterType;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import sk.tuke.gamestudio.entity.Score;
import sk.tuke.gamestudio.game.consoleui.ConsoleUI;
import sk.tuke.gamestudio.game.core.Field;
import sk.tuke.gamestudio.service.*;

@SpringBootApplication
@ComponentScan(excludeFilters = @ComponentScan.Filter(type = FilterType.REGEX,
        pattern = "sk.tuke.gamestudio.server.*"))
public class SpringClient {
    public static void main(String[] args) {
        new SpringApplicationBuilder(SpringClient.class).web(WebApplicationType.NONE).run(args);
    }
    @Bean
    public RestTemplate restTemplate(){return new RestTemplate();}
    @Bean
    public CommandLineRunner runner(ConsoleUI ui) {
        return args -> ui.play();
    }
    @Bean
    public ConsoleUI consoleUI() {
        return new ConsoleUI();
    }
    @Bean
    public Field field() {
        return new Field();
    }
    @Bean
    public ScoreService scoreService() {
        //return new ScoreServiceJPA();
        return new ScoreServiceRestClient();
    }
    @Bean
    public RatingService ratingService() {
        //return new RatingServiceJPA();
        return new RatingServiceRestClient();
    }

    @Bean
    public CommentService commentService() {
        return new CommentServiceJPA();
    }
    @Bean
    public ScoreServiceJPA scoreServiceJPA(){return new ScoreServiceJPA();}
    @Bean
    public RatingServiceJDBC ratingServiceJDBC(){return new RatingServiceJDBC();}
    @Bean
    public ScoreServiceJDBC scoreServiceJDBC(){return new ScoreServiceJDBC();}
    @Bean
    public CommentServiceJDBC commentServiceJDBC(){return new CommentServiceJDBC();}




}
