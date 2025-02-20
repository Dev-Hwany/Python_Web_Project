$(document).ready(function(){
  // CSRF 토큰 가져오기 함수
  function getCookie(name) {
      let cookieValue = null;
      if (document.cookie && document.cookie !== "") {
          let cookies = document.cookie.split(";");
          for (let i = 0; i < cookies.length; i++) {
              let cookie = cookies[i].trim();
              if (cookie.substring(0, name.length + 1) === (name + "=")) {
                  cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                  break;
              }
          }
      }
      return cookieValue;
  }

  // 좋아요 토글
  $(".favorite").click(function(){
    let feed_id = $(this).attr("feed_id");
    let $favorite = $(this);
    let currentText = $.trim($favorite.text());
    // favorite_border이면 좋아요 추가, 아니면 취소
    let adding = (currentText === "favorite_border");
    let newText = adding ? "favorite" : "favorite_border";
    // 즉시 아이콘 업데이트
    $favorite.text(newText);
    $.ajax({
      url: "/feed/like",
      type: "POST",
      data: JSON.stringify({ feed_id: feed_id, favorite_text: currentText }),
      contentType: "application/json",
      headers: { "X-CSRFToken": getCookie("csrftoken") },
      success: function(response) {
         // 좋아요 개수 업데이트 (DOM에 반영)
         let $countSpan = $("#like_count_" + feed_id);
         let currentCount = parseInt($countSpan.text());
         if(adding){
           $countSpan.text(currentCount + 1);
         } else {
           $countSpan.text(currentCount - 1);
         }
      },
      error: function(){
         console.log("좋아요 토글 오류");
      }
    });
  });

  // 북마크 토글
  $(".bookmark").click(function(){
    let feed_id = $(this).attr("feed_id");
    let $icon = $(this);
    let currentText = $icon.text().trim();
    let newText = (currentText === "bookmark") ? "bookmark_border" : "bookmark";
    $icon.text(newText);
    $.ajax({
      url: "/feed/bookmark",
      method: "POST",
      data: JSON.stringify({ feed_id: feed_id, bookmark_text: currentText }),
      contentType: "application/json",
      headers: { "X-CSRFToken": getCookie("csrftoken") }
    });
  });

  // 댓글 작성
  $(".upload_reply").click(function(){
    let feed_id = $(this).attr('feed_id');
    let replyContent = $("#reply_" + feed_id).val().trim();
    if(replyContent === ""){
      alert("댓글을 입력하세요.");
      return;
    }
    $.ajax({
      url: "/feed/reply",
      type: "POST",
      data: { feed_id: feed_id, reply_content: replyContent },
      headers: { "X-CSRFToken": getCookie("csrftoken") },
      success: function(){
        location.reload();
      },
      error: function(xhr){
        alert("댓글 작성 오류: " + (xhr.responseJSON ? xhr.responseJSON.message : "오류 발생"));
      }
    });
  });

  // === 댓글 옵션: 드롭다운 방식 ===

  // "수정" 옵션 클릭 시 인라인 수정 폼 표시
  $(document).on("click", ".edit-comment", function(e){
      e.preventDefault();
      let $replyItem = $(this).closest(".reply-item");
      $replyItem.find(".comment-edit-form").show();
  });

  // "삭제" 옵션 클릭 시 AJAX로 댓글 삭제
  $(document).on("click", ".delete-comment", function(e){
      e.preventDefault();
      if(!confirm("정말 댓글을 삭제하시겠습니까?")) return;
      let $replyItem = $(this).closest(".reply-item");
      let commentId = $replyItem.data("comment-id");
      $.ajax({
         url: "{% url 'comment_delete' 0 %}".replace("0", commentId),
         type: "POST",
         headers: { "X-CSRFToken": getCookie("csrftoken") },
         success: function(response){
            if(response.status === "success"){
              $replyItem.remove();
            } else {
              alert(response.message);
            }
         },
         error: function(xhr){
            alert("댓글 삭제 오류: " + (xhr.responseJSON ? xhr.responseJSON.message : "오류 발생"));
         }
      });
  });

  // "취소" 옵션 클릭 시 (드롭다운 내) 수정 폼 숨김
  $(document).on("click", ".cancel-comment", function(e){
      e.preventDefault();
      let $replyItem = $(this).closest(".reply-item");
      $replyItem.find(".comment-edit-form").hide();
  });

  // 댓글 수정: 인라인 수정 폼의 "저장" 버튼 클릭 시 AJAX 요청
  $(document).on("click", ".save-reply-edit-btn", function(e){
      e.preventDefault();
      let $replyItem = $(this).closest(".reply-item");
      let commentId = $replyItem.data("comment-id");
      let newContent = $replyItem.find(".reply-edit-input").val().trim();
      if(newContent === ""){
         alert("수정할 내용을 입력해 주세요.");
         return;
      }
      $.ajax({
         url: "{% url 'comment_update' 0 %}".replace("0", commentId),
         type: "POST",
         data: { content: newContent },
         headers: { "X-CSRFToken": getCookie("csrftoken") },
         success: function(response){
            if(response.status === "success"){
              // 수정된 내용을 댓글 텍스트에 반영하고 폼 숨김
              $replyItem.find(".comment-text").text(newContent);
              $replyItem.find(".comment-edit-form").hide();
            } else {
              alert(response.message);
            }
         },
         error: function(xhr){
            alert("댓글 수정 오류: " + (xhr.responseJSON ? xhr.responseJSON.message : "오류 발생"));
         }
      });
  });

  // === 답글(중첩 댓글) 기능 ===

  // "답글 달기" 버튼 클릭 시 답글 작성 폼 토글
  $(document).on("click", ".reply-to-comment", function(e){
      e.preventDefault();
      let $replyItem = $(this).closest(".reply-item");
      $replyItem.find(".nested-reply-form").toggle();
  });

  // 답글 작성 폼 "취소" 버튼 클릭 시 폼 숨김
  $(document).on("click", ".cancel-nested-reply-btn", function(e){
      e.preventDefault();
      let $replyItem = $(this).closest(".reply-item");
      $replyItem.find(".nested-reply-form").hide();
  });

  // 답글 작성 폼 "게시" 버튼 클릭 시 AJAX 요청으로 답글 등록
  $(document).on("click", ".submit-nested-reply-btn", function(e){
      e.preventDefault();
      let $replyItem = $(this).closest(".reply-item");
      let parentCommentId = $replyItem.data("comment-id");
      let replyContent = $replyItem.find(".nested-reply-input").val().trim();
      if(replyContent === ""){
         alert("답글 내용을 입력해 주세요.");
         return;
      }
      $.ajax({
         url: "{% url 'comment_reply' 0 %}".replace("0", parentCommentId),
         type: "POST",
         data: { reply_content: replyContent },
         headers: { "X-CSRFToken": getCookie("csrftoken") },
         success: function(response){
            if(response.status === "success"){
              let newReplyHtml = '<div class="nested-reply-item" data-comment-id="'+response.reply.id+'">' +
                                 '<strong>'+response.reply.nickname+'</strong> ' +
                                 '<span class="comment-text">'+response.reply.reply_content+'</span>' +
                                 '</div>';
              $replyItem.find(".nested-replies").append(newReplyHtml);
              $replyItem.find(".nested-reply-form").hide();
              $replyItem.find(".nested-reply-input").val("");
            } else {
              alert(response.message);
            }
         },
         error: function(xhr){
            alert("답글 작성 오류: " + (xhr.responseJSON ? xhr.responseJSON.message : "오류 발생"));
         }
      });
  });
});
