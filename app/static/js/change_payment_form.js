window.addEventListener("load", function () {
  (function ($) {
    $(document).ready(function () {
      var paymentTypeField = $('#id_payment_type');
      var targetAccountField = $('#id_targed_account');
      function toggleTargetAccountField() {
        var paymentType = paymentTypeField.val();
        targetAccountField.prop('disabled', paymentType !== 'transfer');

        if (paymentType !== 'transfer') {
          targetAccountField.val('');
          $('#add_id_targed_account').hide();
          $('#change_id_targed_account').removeAttr('href');
          $('#delete_id_targed_account').removeAttr('href');
          $('#view_id_targed_account').removeAttr('href');
        }
        else {
          $('#add_id_targed_account').show();
          $('#change_id_targed_account').attr('href', originalHref);
          $('#delete_id_targed_account').attr('href', originalHref);
          $('#view_id_targed_account').attr('href', originalHref);
        }
      }
      toggleTargetAccountField();
      paymentTypeField.on('change', toggleTargetAccountField);
    });
  })(django.jQuery);
});