+++
Categories = ["test", "code"]
Description = ""
Tags = ["code"]
date = "2014-11-09T03:32:39+01:00"
title = "Code test"

draft = true
+++

Here I will try inserting code, both using markdown and the hugo highlighting shortcode

# Go

Using markdown: This is a median randomized algorithm

```
func randomizedMedian(s []int) (m int, err error) {
    n := float64(len(s))
    n34 := math.Pow(float64(n), 3.0/4.0)
    r := randSampleWithRep(s, int(math.Ceil(n34)))
    sort.Ints(r)
    d := r[int(math.Floor(1.0/2.0 * n34 - math.Sqrt(n))) - 1]
    u := r[int(math.Ceil(1.0/2.0 * n34 + math.Sqrt(n))) - 1]
    c := filter(s, func(x int) bool { return d <= x && x <= u })
    ld := count(s, func(x int) bool { return x < d })
    lu := count(s, func(x int) bool { return x > u })
    //fmt.Println("d:", d, "u:", u, "ld:", ld, "lu:", lu)
    if float64(ld) > n/2 && float64(lu) < n/2 {
        return 0, fmt.Errorf("Fail")
    }
    if float64(len(c)) <= 4.0 * n34 {
        sort.Ints(c)
    } else {
        return 0, fmt.Errorf("Fail")
    }
    return c[int(math.Floor(n/2)) - ld + 1 - 1], nil
}
```

This would be a bash line:

    $ sudo rm -rf /

But now I want it with syntax highlighting

Using gist: This is quickselect

{{% gist "Dhole/b5186c2c4f0e27d43c11" %}}

# C

Show some love to plain old school C

This is the main loop of my gameboy emulator, using SDL_GetTicks() function to syncronize
the framerate

{{% gist "Dhole/b9e4e1a28d5a2eed2f00" %}}
