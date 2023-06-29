package sk.tuke.gamestudio.entity;


import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.Id;
import javax.persistence.NamedQuery;
import java.io.Serializable;

@Entity
@NamedQuery(name = "Users.getUsers",
        query = "SELECT u FROM Users u ORDER BY u.login")
public class Users implements Serializable {

    @Id
    @GeneratedValue
    private int ident;

    private String login;
    private String password;


    public Users() {
    }

    public Users(String login, String password) {
        this.login = login;
        this.password = password;
    }


    public String getPassword() {
        return password;
    }

    public void setPassword(String password) {
        this.password = password;
    }

    public String getLogin() {
        return login;
    }

    public void setLogin(String login) {
        this.login = login;
    }

    public int getIdent() {
        return ident;
    }

    public void setIdent(int ident) {
        this.ident = ident;
    }
}
