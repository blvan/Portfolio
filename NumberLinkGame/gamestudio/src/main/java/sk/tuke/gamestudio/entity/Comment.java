package sk.tuke.gamestudio.entity;

import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.Id;
import java.io.Serializable;
import java.util.Date;
import java.io.Serializable;

@Entity
/*@NamedQuery( name = "Comment.getComments",
        query = "SELECT s FROM Comment s WHERE s.game=:game")
@NamedQuery( name = "Comment.resetComments",
        query = "DELETE FROM Comment")*/
public class Comment  implements Serializable {
    @Id
    @GeneratedValue
    private int ident;
    private String comment;
    private String game;
    private String player;

    public Comment(String game,String comment, String player) {
        this.comment = comment;
        this.game = game;
        this.player = player;
    }
    public int getIdent() { return ident; }
    public void setIdent(int ident) { this.ident = ident; }
    public Comment() {

    }
    public String getGame() {
        return game;
    }

    public String getComment() {
        return comment;
    }

    public void setComment(String comment) {
        this.comment = comment;
    }

    public String getPlayer() {
        return player;
    }

    public void setPlayer(String player) {
        this.player = player;
    }

    @Override
    public String toString() {
        return "Comment{" +
                "Comment:'" + comment + '\'' +
                ", player='" + player + '\'' +
                '}';
    }
}
