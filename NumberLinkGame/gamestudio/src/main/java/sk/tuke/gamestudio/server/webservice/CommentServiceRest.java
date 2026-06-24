package sk.tuke.gamestudio.server.webservice;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import sk.tuke.gamestudio.entity.Comment;
import sk.tuke.gamestudio.entity.Rating;
import sk.tuke.gamestudio.service.CommentException;
import sk.tuke.gamestudio.service.CommentService;
import sk.tuke.gamestudio.service.RatingException;
import sk.tuke.gamestudio.service.RatingService;

import java.util.List;

@RestController
@RequestMapping("/api/comment")
public class CommentServiceRest {
    @Autowired
    private CommentService commentService;

    @PostMapping("/{game}")
    public void addComment(@RequestBody Comment comment) throws CommentException{
        commentService.addComment(comment);
    }

    @GetMapping("/{game}")
    public List<Comment> getComments(@PathVariable String game){
     return commentService.getComments(game);
    }

}
