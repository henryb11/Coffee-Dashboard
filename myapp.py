import pandas as pd
import streamlit as st
import plotly.express as px
import re

st.set_page_config(page_title="Coffee Dashboard",
                   page_icon=":coffee:",
                   layout = "wide")

# -- Prepping Data -- 
@st.cache_data
def load_data():
    df = pd.read_excel('df_arabica_clean.xlsx')
    df = df.drop('Unnamed: 0', axis = 1)
    df.columns = df.columns.str.lower()
    df.rename(columns={'country of origin': 'country_of_origin', 'farm name': 'farm_name', 
                    'lot number': 'lot_number', 'ico number': 'ico_number', 'number of bags': 'number_of_bags', 
                    'bag weight': 'bag_weight', 'in-country partner': 'in_country_partner', 
                    'harvest year': 'harvest_year', 'grading date': 'grading_date', 
                    'processing method': 'processing_method', 'clean cup': 'clean_cup', 
                    'total cup points': 'total_cup_points', 'moisture percentage': 'moisture_percentage', 
                    'category one defects': 'category_one_defects', 'category two defects': 'category_two_defects', 
                    'certification body': 'certification_body', 'certification address': 'certification_address', 
                    'certification contact': 'certification_contact'}, inplace=True)
    df = df.drop(['mill','ico_number','producer','in_country_partner','owner','status','defects','quakers','certification_body','certification_address','certification_contact'],axis=1)

    def upd_alt(row):

        alt = row['altitude']
        try: 
            alt = int(alt)
            return alt 
        except: 
            try: 
                list = re.findall(r'\d+', alt)
                value_1 = int(list[0])
                value_2 = int(list[-1])
                return int((value_1 + value_2) / 2)
            except:
                return 'na'
    df['altitude'] = df.apply(upd_alt, axis=1)
    df.drop(df[df.altitude == 'na'].index, inplace=True)

    def gross_mass (row):
        
        bag_mass = row['bag_weight']
        bag_mass = re.search(r'\d+',bag_mass).group()
        
        num_bags = int(row['number_of_bags'])
        
        return int(bag_mass)*num_bags

    df['total_mass'] = df.apply(gross_mass, axis=1)
    return df

coffee= load_data()

# --- Sidebar ---
st.sidebar.header("Please filter here:")
country = st.sidebar.multiselect(
    "Select country:",
    options=coffee['country_of_origin'].unique(),
    default=coffee['country_of_origin'].unique()
)

alt = st.sidebar.slider(
    'Select an altitude range (meters above sea level)',
    500, 3000, (100, 5500))

harvest_year = st.sidebar.multiselect(
    "Select harvest year:",
    options=coffee['harvest_year'].unique(),
    default=coffee['harvest_year'].unique()
)

coffee_selection = coffee.query(
    'country_of_origin == @country &  harvest_year == @harvest_year'
)
agree = st.sidebar.checkbox('Remove Yhaenu Plc Farm?')

if agree:
    st.write('Okay')
    coffee_selection = coffee_selection[coffee_selection['farm_name']!='YHAENU PLC FARM']

coffee_selection = coffee_selection[coffee_selection['altitude'].between(alt[0],alt[1])]

# --- Main Page ---
st.title(":coffee: Coffee Dashboard")
st.markdown("##")

# Top KPI's

total_mass = int(coffee_selection['total_mass'].sum())
average_rating = round(coffee_selection['total_cup_points'].mean(),1)
star_rating = ":star:"*int(round(average_rating/10,0))
average_mass_per_farm = int(round(coffee_selection['total_mass'].median(),0))

left_column, middle_column, right_column = st.columns(3)
with left_column:
    st.subheader("Total Mass:")
    st.subheader(f"{total_mass:,} KG")
with middle_column:
    st.subheader("Average Rating:")
    st.subheader(f"{average_rating} {star_rating}")
with right_column:
    st.subheader("Average (median) mass per farm:")
    st.subheader(f"{average_mass_per_farm} KG")

st.markdown("---")


# Product by country [bar chart]
product_by_country = coffee_selection.groupby(by=["country_of_origin"]).sum().sort_values(by='total_mass', ascending=False)


fig_country_product = px.bar(
    product_by_country,
    x='total_mass',
    y=product_by_country.index,
    labels={'country_of_origin': 'Country', 'total_mass' : 'Amount of Coffee Exported in Kilograms'},
    orientation="h",
    title="<b> Gross Product by Country </b>",
    color_discrete_sequence=["#0083B8"]*len(product_by_country)
)



# rating by country [bar chart]
rating_by_country = (

    coffee_selection.groupby(by=["country_of_origin"]).mean()[['total_cup_points']].sort_values(by='total_cup_points', ascending=False)
)

fig_country_rating = px.bar(
    rating_by_country,
    x='total_cup_points',
    labels={'country_of_origin': 'Country', 'total_cup_points' : 'Total Coffee Quality Rating'},
    range_x=(80,90),
    y=rating_by_country.index,
    orientation="h",
    title="<b> Average rating by Country </b>"
)

# rating per variety
top_8 = ['Caturra', 'Gesha', 'Typica', 'Bourbon', 'Catuai', 'unknown', 'Catimor','Ethiopian Heirlooms']

rating_by_variety = (
    coffee[coffee['variety'].isin(top_8)].groupby(by=["variety"]).mean()[['total_cup_points']].sort_values(by='total_cup_points', ascending=False)
)

fig_variety_rating = px.bar(
    rating_by_variety,
    x='total_cup_points',
    labels={'variety': 'Type of Bean', 'total_cup_points' : 'Total Coffee Quality Rating'},
    range_x=(80,90),
    y=rating_by_variety.index,
    orientation="h",
    title="<b> Average rating by Variety </b>"
)


left_column, right_column = st.columns(2)

left_column.plotly_chart(fig_country_product, use_container_width= True)
right_column.plotly_chart(fig_country_rating, use_container_width=True)

st.markdown("""
Ethiopia's production dwarfs the rest of the countries in this dataset. A quick google search will show that actually brazil is the largest coffee producing country in the world.
This can be interpreted that the dataset is not meant to be a representation of world coffee producers, but more to highlight other features of coffee.



_There is one farm in particular that completely ruins the database for everyone else. 'YHAENU PLC FARM'._ 

_Use the filter in the sidebar to cancel this farm out._


""")

st.markdown("---")
left_column, right_column = st.columns(2)
left_column.plotly_chart(fig_variety_rating, use_container_width= True)

right_column.markdown("""
## Coffee Varieties. 

Here we can see the top 8 coffee varieties and how they score on the total cup score. A 'cupping' is essentially a formal coffee review. 
Not unlike sommeliers, coffee tasters by necessity leave a large part of the coffee's score to the subjective realm. Despite this, it seems that
Geisha coffee strains are the highest rated and this is a good indicator why there are more individual farms growing this type of bean.
""")
right_column.write(coffee['variety'].value_counts().head(8), use_container_width = True)

st.markdown("---")

mass_variety_country = coffee_selection.groupby(by=['variety']).sum().sort_values(by='total_mass', ascending=False).head(20)
st.markdown("""
# So what is the best variety of coffee? 
Ethiopian heirlooms seem to be the highest mass produced and also happen to be one of the highest-rated coffees. It is no surprise that there is a farm in ethiopia that produces 
so much of this style of bean. However, when we remove this farm from our dashboard, we see that Gesha by mass is no where near the top produced bean.
This may be because gesha is a more sensitive strain of plant to the environment and the other strains are more hardy and able to be produced at a good standard.


Besides the Ethiopian heirloom coffees, Carurra, Mundo Novo, and Bourbon strains are the most grown by mass. There are less farmers that grow these coffees but more volume yeilded.


""")
fig_mvc = px.bar(
    mass_variety_country,
    y=mass_variety_country.index,
    x='total_mass'
    
)
st.plotly_chart(fig_mvc, use_container_width= True)

# --- hide style ---
hide_st_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)