from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from carts.models import CartItem
from .forms import OrderForm
import datetime
from .models import Order, Payment, OrderProduct
import json
from store.models import Product
import razorpay
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings


# Initialize Razorpay Client
client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def initiate_payment(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user, is_ordered=False)

    # Razorpay requires amount in paise (multiply by 100)
    payment_data = {
        "amount": int(round(order.order_total, 2) * 100),
        "currency": "INR",
        "receipt": str(order.order_number),
        "payment_capture": "1"
    }

    # Create order in Razorpay
    razorpay_order = client.order.create(data=payment_data)

    # Store Razorpay Order ID in session
    request.session["razorpay_order_id"] = razorpay_order["id"]

    context = {
        "order": order,
        "razorpay_order_id": razorpay_order["id"],
        "grand_total": order.order_total
    }
    return render(request, "orders/payment.html", context)


def payments(request):
    if request.method == "POST":
        try:
            body = json.loads(request.body)
            print("Received Payment Data:", body)

            # if not body.get("razorpay_order_id"):
            #     return JsonResponse({"success": False, "error": "Missing razorpay_order_id"}, status=400)

            order = get_object_or_404(Order, user=request.user, is_ordered=False, order_number=body["orderID"])

            # Verify Razorpay Payment Signature
            params_dict = {
                "razorpay_payment_id": body["razorpay_payment_id"],
                
                # "razorpay_signature": body["razorpay_signature"]
            }

            # try:
            #     client.utility.verify_payment_signature(params_dict)
            #     print("Payment Verified Successfully!")
            # except razorpay.errors.SignatureVerificationError:
            #     return JsonResponse({"success": False, "error": "Payment verification failed"}, status=400)

            # Save the payment
            payment = Payment.objects.create(
                user=request.user,
                payment_id=body["razorpay_payment_id"],
                payment_method="Razorpay",
                amount_paid=order.order_total,
                status="Paid",
            )

            # Update order
            order.payment = payment
            order.is_ordered = True
            order.save()

            # Move cart items to order products
            cart_items = CartItem.objects.filter(user=request.user)

            for item in cart_items:
                orderproduct = OrderProduct.objects.create(
                    order=order,
                    payment=payment,
                    user=request.user,
                    product=item.product,
                    quantity=item.quantity,
                    product_price=item.product.price,
                    ordered=True
                )
                orderproduct.variations.set(item.variations.all())
                orderproduct.save()

                # Reduce stock
                item.product.stock -= item.quantity
                item.product.save()

            # Clear cart
            cart_items.delete()

            # Send confirmation email
            mail_subject = 'Thank you for your order!'
            message = render_to_string('orders/order_recieved_email.html', {'user': request.user, 'order': order})
            to_email = request.user.email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.content_subtype = "html"
            send_email.send()

            return JsonResponse({
                "success": True,
                "order_number": order.order_number,
                "payment_id": payment.payment_id,
                
            })

        except Exception as e:
            print("Error Processing Payment:", str(e))
            return JsonResponse({"success": False, "error": str(e)}, status=400)

    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)



def place_order(request, total=0, quantity=0,):
    current_user = request.user

    # If the cart count is less than or equal to 0, then redirect back to shop
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('store')

    grand_total = 0
    tax = 0
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    tax = round((8 * total) / 100, 2)
    grand_total = round(total + tax, 2)

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # Store all the billing information inside Order table
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.country = form.cleaned_data['country'] if 'country' in form.cleaned_data else 'India'  # Fix here  
            data.pincode = form.cleaned_data['pincode']
            data.state = form.cleaned_data['state']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()
            # Generate order number
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr,mt,dt)
            current_date = d.strftime("%Y%m%d") #20210305
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
            context = {
                'order': order,
                'cart_items': cart_items,
                'total': total,
                'tax': tax,
                'grand_total': grand_total,
            }
            return render(request, 'orders/payments.html', context)
            
    else:
        return redirect('checkout')
    

def order_complete(request):
    order_number = request.GET.get('order_number')
    transID = request.GET.get('payment_id')
    transID = request.GET.get('payment_id')

    if not order_number or not transID:
        return redirect('home')  # Redirect if parameters are missing

    try:
        order = get_object_or_404(Order, order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order=order)

        subtotal = sum(item.product_price * item.quantity for item in ordered_products)

        try:
            payment = get_object_or_404(Payment, payment_id=transID)
        except Payment.DoesNotExist:
            return redirect('home')

        context = {
            'order': order,
            'ordered_products': ordered_products,
            'order_number': order.order_number,
            'transID': payment.payment_id,
            'payment': payment,
            'subtotal': subtotal,
        }
        return render(request, 'orders/order_complete.html', context)

    except Order.DoesNotExist:
        return redirect('home')
