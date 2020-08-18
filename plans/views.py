from django.shortcuts import render, get_object_or_404, redirect
from .forms import CustomSignupForm
from django.urls import reverse_lazy
from django.views import generic
from .models import BlogPlan, Customer
from django.contrib.auth import authenticate, login
#new decorator import to use in the login so that without login no can do any checkout
from django.contrib.auth.decorators import login_required, user_passes_test
#the private key shouldn't be seen by anyone, hence we need to keep it here.
import stripe
from django.http import HttpResponse

stripe.api_key = "sk_test_51HFCSdElso1Ez1pccldzD4KPoMUrlk7XcwSMFZEIHLWVNBV6HkiMsAlFskcvf9WcGqjFHviKOrm1MRjVFYHXGEvj00O6hBd67V"

#this updateaccounts function is only for the admins to periodically check if the credit card information 
# is still good or when they are posting new contents the customers are getting those perfectly.
# For this reason, in the urls.py, a new path has also been created to do so


# this decorator needs to be imported
@user_passes_test(lambda u: u.is_superuser)
def updateaccounts(request):
    customers = Customer.objects.all()
    for customer in customers:
        subscription = stripe.Subscription.retrieve(customer.stripe_subscription_id)
        if subscription.status != 'active':
            customer.membership = False
        else:
            customer.membership = True
        customer.cancel_at_period_end = subscription.cancel_at_period_end
        customer.save()
        return HttpResponse('completed')


def home(request):
    plans = BlogPlan.objects
    return render(request, 'plans/home.html', {'plans':plans})

def plan(request,pk):
    plan = get_object_or_404(BlogPlan, pk=pk)
    if plan.premium:
        # checking whether the user is authenticated, and if
        # has an membership, redirecting to plan page, if no membership, then to join route
        if request.user.is_authenticated:
            try:
                if request.user.customer.membership:
                    return render(request, 'plans/plan.html', {'plan':plan})
            except Customer.DoesNotExist:
               return redirect('join') 
        return redirect('join')
    else:
        return render(request, 'plans/plan.html', {'plan':plan})

def join(request):
    return render(request, 'plans/join.html')
#new
@login_required
def checkout(request):
   
    # if already a member, then don't purchase the same subscription twice, so redirecting to the 
    # settings page
    try:
        if request.user.customer.membership:
            return redirect('settings')
    except Customer.DoesNotExist:
        pass
    
    #coupon accepting 
    coupons = {'halloween':31, 'welcome': 10}
    if request.method == 'POST':
        stripe_customer = stripe.Customer.create(email=request.user.email, source=request.POST['stripeToken'])
        plan = 'price_1HFCvSElso1Ez1pchXwUxj1N'
        if request.POST['plan'] == 'yearly':
            plan = 'price_1HFCwBElso1Ez1pcy9k2RZAF'
        if request.POST['coupon'] in coupons:
            percentage = coupons[request.POST['coupon'].lower()]
            try:
                coupon = stripe.Coupon.create(duration='once', id=request.POST['coupon'].lower(),
                percent_off=percentage)
            except:
                pass
            subscription = stripe.Subscription.create(customer=stripe_customer.id,
            items=[{'plan':plan}], coupon=request.POST['coupon'].lower())
        else:
            subscription = stripe.Subscription.create(customer=stripe_customer.id,
            items=[{'plan':plan}])
        # the next whole customer block is for stripe to save all the information
        customer = Customer()
        customer.user = request.user
        customer.stripeid = stripe_customer.id
        customer.membership = True
        customer.cancel_at_period_end = False
        customer.stripe_subscription_id = subscription.id
        customer.save()
        return redirect('home')
        # this if condition is to check whether the payment has been done succesfully, after that
    # redirect to the homepage, otherwise stay at the payment page in the else block
    # the test card number is 4242 4242 4242 4242 , CVC 222, date nay future date
    else:
        plan = 'monthly'
        coupon = "none"
        price = 1000 #penny
        original_dollar = 10
        coupon_dollar = 0
        final_dollar = 10
        if request.method == "GET" and "plan" in request.GET:
            if request.GET['plan'] == 'yearly':
                plan = 'yearly'
                price = 10000 #penny
                original_dollar = 100
                final_dollar = 100

        if request.method == "GET" and "coupon" in request.GET:
            if request.GET['coupon'].lower() in coupons:
                coupon = request.GET['coupon'].lower()
                percentage = coupons[coupon]
                coupon_price = int((percentage/100)*price)
                price -= coupon_price
                coupon_dollar = str(coupon_price)[:-2] + '.' + str(coupon_price)[-2:]
                final_dollar = str(price)[:-2] + '.' + str(price)[-2:]

        return render(request, 'plans/checkout.html',{'plan': plan, 'coupon': coupon, 'price': price,
        'original_dollar': original_dollar, 'coupon_dollar': coupon_dollar, 'final_dollar': final_dollar})

def settings(request):
    # if they want to cancel the subscription
    membership = False
    cancel_at_period_end = False
    if request.method == 'POST':
        subscription = stripe.Subscription.retrieve(request.user.customer.stripe_subscription_id)
        subscription.cancel_at_period_end = True
        request.user.customer.cancel_at_period_end = True
        cancel_at_period_end = True
        subscription.save()
        request.user.customer.save()
    else:
        try:
            if request.user.customer.membership:
                membership = True
            if request.user.customer.cancel_at_period_end:
                cancel_at_period_end = True
        except Customer.DoesNotExist:
            membership = False
    return render(request, 'registration/settings.html', {'membership': membership, 
    'cancel_at_period_end' : cancel_at_period_end})

class SignUp(generic.CreateView):
    form_class = CustomSignupForm
    success_url = reverse_lazy('home')
    template_name = 'registration/signup.html'

    def form_valid(self, form):
        valid = super(SignUp, self).form_valid(form)
        username, password = form.cleaned_data.get('username'), form.cleaned_data.get('password1')
        new_user = authenticate(username=username, password=password)
        login(self.request, new_user)
        return valid
