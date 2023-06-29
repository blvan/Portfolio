package sk.tuke.gamestudio.entity;

import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.Id;
import javax.persistence.NamedQuery;
import java.io.Serializable;
import java.sql.Timestamp;
import java.util.Date;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.List;

@Entity
@NamedQuery(name = "Rating.checkRating",
        query = "SELECT r FROM Rating r WHERE r.game=:game AND r.player=:player")
@NamedQuery( name = "Rating.getAverageRating",
        query = "SELECT AVG(r.rating) FROM Rating r WHERE r.game=:game")
@NamedQuery( name = "Rating.getRating",
        query = "SELECT r FROM Rating r WHERE r.game=:game ORDER BY r.rating DESC")
@NamedQuery( name = "Rating.getRatings",
        query = "SELECT s FROM Comment s WHERE s.game=:game")
@NamedQuery( name = "Rating.resetRating",
        query = "DELETE FROM Score")

public class Rating implements Serializable {
    @Id
    @GeneratedValue
    private int ident;
    private String player;

    private int rating;
    private String game;
    //private List<> getRatings = new ArrayList<>();
    //Timestamp ratedOn
    public Rating(String player, String game, int rating) {
        this.game = game;
        this.player = player;
        this.rating = rating;
     // this.ratedOn = ratedOn;
    }

    public Rating() {

    }
    public String getGame() {
        return game;
    }
    public void setGame(String game) {
        this.game = game;
    }
    public int getIdent() { return ident; }
    public void setIdent(int ident) { this.ident = ident; }
    public String getPlayer() {
        return player;
    }

    public void setPlayer(String player) {
        this.player = player;
    }

    public int getRating() {
        return rating;
    }

    public void setRating(int rating) {
        this.rating = rating;
    }
   /* public Timestamp getRatedOn() {
        return ratedOn;
    }
    public void setRatedOn(Timestamp ratedOn) {
        this.ratedOn = ratedOn;
    }*/

    @Override
    public String toString() {
        return "Rating{" +
                "rating='" + rating + '\'' +
                ", player='" + player + '\'' +
                '}';
    }
}
